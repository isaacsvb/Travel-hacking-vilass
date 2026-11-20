# Design — Backend de Milhas (módulo OPCIONAL)

> **Status: OPCIONAL.** Deliverable principal é o Travel Hacking Toolkit (`.kiro/specs/travel-hacking-toolkit/`). Este backend é um serviço Python autônomo de monitoramento + alertas, para quem quer vigilância contínua rodando fora do agente interativo.

## Visão geral

Serviço Python dirigido por agendador que roda um pipeline de quatro etapas por rota monitorada:

```
busca (disponibilidade) → match (sweet spots + alcançabilidade) → valor (CPM) → alerta (n8n / Telegram)
```

É **API-licenciada-primeiro** e **free-first**: a seats.aero (cache keyless ~60 dias; Pro opcional para ao vivo/alertas) é a fonte primária de disponibilidade-prêmio; a Duffel (busca grátis) fornece a comparação em dinheiro; um coletor Playwright é fallback **opt-in, desligado por padrão**. Uma base de conhecimento em arquivos (reaproveitada do toolkit) guarda alianças, caminhos de reserva, sweet spots, razões de transferência e valuations. Uma calculadora de valor pura transforma dados em oportunidades ranqueadas por CPM, que são deduplicadas, persistidas e enviadas aos canais de notificação.

### Fatos externos verificados (no momento desta spec)

- **seats.aero Partner API**: cached search, bulk por programa, busca ao vivo em ~20 programas, 70.000+ rotas, alertas, com quotas no Pro. [docs seats.aero](https://developers.seats.aero/reference/getting-started-p).
- **Kiwi Tequila** fechou cadastro self-serve (canal B2B) e **Amadeus Self-Service** está marcado para desligamento/migração em 2026 — tratar como fontes de dinheiro gated. [vervotech](https://www.vervotech.com/hub/integrations/tequila-api/), [thunderbit](https://thunderbit.com/blog/best-flight-api-with-free-tiers).
- **Duffel** segue self-serve para busca em dinheiro → fonte padrão de cash.

*(Conteúdo das fontes externas reformulado para conformidade de licença.)*

---

## Arquitetura

```
                         ┌─────────────────────────────────────────────┐
                         │                Agendador                     │
                         │  (APScheduler / cron)  — dispara jobs         │
                         └───────────────────┬─────────────────────────┘
                                             │  MonitorJob
                                             ▼
   ┌──────────────────────────────── Pipeline (por job) ──────────────────────────────┐
   │  1. BUSCA            2. MATCH              3. VALOR            4. ALERTA            │
   │  Agregador de        Matcher sweet-spot    Calc CPM            n8n webhook          │
   │  disponibilidade  →  + alcançabilidade  →  (função pura)   →   Telegram             │
   └─────────┬───────────────────┬─────────────────────┬──────────────────────────────┘
             │                    │                     │
   ┌─────────▼─────────┐  ┌───────▼────────┐   ┌────────▼────────┐
   │ Adaptadores de    │  │ Base de         │   │ Dedup + cooldown │
   │ fonte             │  │ conhecimento    │   │ + persistência   │
   │ • seats.aero (API)│  │ (JSON validado) │   └────────┬────────┘
   │ • Duffel (cash)   │  │ data/*.json      │            │
   │ • Playwright      │  └─────────────────┘    ┌────────▼───────┐
   │   (opt-in)        │                          │ Datastore       │
   └─────────┬─────────┘   ┌──────────────────┐  │ (SQLite/PG)     │
             │             │ Observabilidade:  │  └────────────────┘
   ┌─────────▼─────────┐   │ logs + /health    │
   │ Camada resiliência│   │ /metrics          │
   │ retry, rate limit,│   └──────────────────┘
   │ circuit breaker   │
   └───────────────────┘
```

### Módulos

```
backend_milhas/
├── app/            config.py, scheduler.py, pipeline.py
├── sources/        base.py, seats_aero.py, duffel.py, scrapers/{base,<programa>}.py
├── knowledge/      loader.py, schemas.py  (lê data/*.json do toolkit)
├── domain/         models.py, matcher.py, calculator.py (puro)
├── alerts/         base.py, n8n.py, telegram.py
├── infra/          resilience.py, persistence.py, logging.py
└── api/            server.py (FastAPI: health, metrics, trigger manual)
```

---

## Componentes e interfaces

### Modelos canônicos (`domain/models.py`)

Todas as fontes normalizam para um schema (Req 1.3, 2.5):

```python
@dataclass(frozen=True)
class Availability:
    origin: str; destination: str; date: date
    program: str; operating_carrier: str; cabin: Cabin
    miles_cost: int | None          # None => desconhecido, nunca descartar (Req 1.4)
    cash_fees: Money | None          # taxas + sobretaxas do prêmio
    seats: int | None
    source: str                      # "seats_aero" | "duffel" | "scraper:<prog>"
    last_seen: datetime              # frescor (Req 1.5)
    @property
    def is_stale(self) -> bool: ...

@dataclass(frozen=True)
class Opportunity:
    availability: Availability; booking_path: BookingPath
    cpm: float | None; cash_price: Money | None
    reachable: bool; sweet_spot_id: str | None
    needs_verification: bool; dedup_key: str
```

### Adaptadores de fonte (`sources/`)

Protocolo comum para fan-out e merge:

```python
class AvailabilitySource(Protocol):
    name: str
    def supports(self, program: str) -> bool: ...
    async def search(self, q: AvailabilityQuery) -> list[Availability]: ...
```

- **`seats_aero.py` (primário, Req 1):** cached/bulk para abrangência + live para rotas configuradas; respeita quotas Pro via rate limiter; `source="seats_aero"`.
- **`duffel.py` (cash, Req 4):** tarifas pagas comparáveis para alimentar o CPM.
- **`scrapers/` (fallback, Req 2):** base `BrowserCollector` — desligado por padrão, pacing/isolamento, falha-alto em bloqueio/CAPTCHA, mesmo schema de saída.

O **agregador** consulta fontes que `supports(program)`, mescla por `(origem, destino, data, programa, companhia, cabine)`, prefere o registro mais fresco não-stale e mantém os stale sinalizados. Distingue **erro** de **vazio** — erro nunca vira "sem disponibilidade".

### Base de conhecimento (`knowledge/`, Req 3)

Lê os mesmos `data/*.json` do toolkit (alliances, partner-awards, sweet-spots, transfer-partners, points-valuations), cada um validado por schema pydantic e com `last_updated` + validade. Falha/degrada apontando o registro problemático; edição sem código.

### Calculadora de valor (`domain/calculator.py`, Req 4) — pura

```python
def compute_cpm(cash_price: Money, award_fees: Money, miles: int) -> float: ...
def classify_value(program: str, cpm: float, valuations: Valuations) -> ValueClass: ...
def effective_miles(direct: int, transfers: list[TransferPath]) -> int: ...
```

Inclui todo custo em dinheiro do prêmio (Req 4.2); sem tarifa comparável → valuation de referência + `preço_indisponível` (Req 4.5); anota sweet spot e desvio observado-vs-esperado (Req 4.6).

### Matcher (`domain/matcher.py`, Req 5)

1. Por `Availability`, consulta `partner-awards` para achar quais programas emitem na companhia operadora.
2. Alcançabilidade por saldo do usuário (direto ou via transferência em `transfer-partners`).
3. Monta `dedup_key` estável; emite `Opportunity` só quando alcançável **e** alto valor, com `needs_verification` se stale.
4. Suprime reemissões salvo mudança material (apoiado na persistência).

### Alertas (`alerts/`, Req 6)

`AlertChannel` com canais independentes: `n8n.py` (POST JSON estável + idempotência) e `telegram.py` (resumo legível via Bot API). Cooldown por oportunidade; payloads sem segredos.

### Resiliência & observabilidade (`infra/`, Req 9)

Retry+backoff+jitter em todas as chamadas; token-bucket por provedor ciente das quotas da seats.aero; circuit breaker por provedor; logs estruturados com id de correlação; `/health` e `/metrics`.

### Persistência (`infra/persistence.py`, Req 10)

SQLite (dev) / Postgres (prod) via SQLAlchemy; tabelas `availability_snapshots`, `opportunities`, `alert_log`; sustenta dedup/cooldown e expurgo por retenção.

---

## Gargalos de captura de dados (análise solicitada)

1. **Scraping de inventário-prêmio viola ToS e é bloqueado** (Akamai/DataDome/PerimeterX). Mitigação: API-primeiro; scraping opt-in, rate-limited, isolado, falha-alto; docs exigem aceite (Req 2, 8.4).
2. **"Sem resultado" é ambíguo** — scrape bloqueado/erro de API parece "sem assento". Mitigação: fontes levantam falha estruturada; agregador separa erro de vazio (Req 2.4, 1.6).
3. **Frescor vs verdade** — cache da seats.aero some antes de emitir. Mitigação: `last_seen`, flag `stale`, `needs_verification` (Req 1.5, 5.4).
4. **Limites e quotas** — fan-out estoura quota rápido. Mitigação: token-bucket + breaker + preferência por cache/bulk (Req 9.2).
5. **Drift de schema** — cada programa/site nomeia cabine/tarifa/taxas diferente e muda sem aviso. Mitigação: `Availability` canônico, mapeamento no adaptador, nulos explícitos, detecção de mudança de layout (Req 1.3–1.4, 2.4).
6. **Precisão de taxas → CPM** — ignorar YQ faz "ótimo" virar medíocre. Mitigação: `cash_fees` first-class e obrigatório no CPM (Req 4.2, 4.5).
7. **Fontes de dinheiro gated** — Kiwi/Amadeus self-serve sumindo. Mitigação: Duffel padrão; fontes plugáveis; sem cash → `preço_indisponível` (Req 4.5).
8. **Desvalorização da base** — tabelas fixas mudam muito. Mitigação: datasets versionados, validados, com validade e flag de desvio (Req 3.6, 4.6).
9. **Spam de alerta** — polling reencontra a mesma oportunidade. Mitigação: `dedup_key` + detecção de mudança material + cooldown (Req 5.5, 6.5).

---

## Tratamento de erros

| Falha | Comportamento |
|---|---|
| API 401/403 | falha a fonte, backoff, mantém as outras (Req 1.6, 9.1) |
| 429 / quota | adia via rate limiter (Req 9.2) |
| erro sustentado | abre circuit breaker, degrada (Req 9.5) |
| scrape bloqueado/CAPTCHA | aborta alvo, motivo estruturado, cai para cache (Req 2.4) |
| arquivo KB inválido | falha/degrada apontando registro (Req 3.5) |
| segredo faltando | falha só o recurso, roda o resto (Req 8.3) |
| falha de canal de alerta | retry com backoff, não bloqueia o outro (Req 6.4) |

## Estratégia de testes

- **Unit:** calculadora (pura, exaustiva), matcher (alcançabilidade/parceiros), validação da KB.
- **Adaptador:** cada fonte contra **fixtures gravadas** (sem chamadas ao vivo no CI).
- **Scraper:** snapshots de HTML incluindo página de bloqueio (asserção de falha-alto).
- **Integração:** pipeline completo sobre fixtures → oportunidades, dedup, payloads de alerta (n8n/Telegram mockados).
- **Resiliência:** retry/backoff, rate-limit, circuit breaker via injeção de falha.

## Escolhas técnicas

| Tema | Escolha | Porquê |
|---|---|---|
| Runtime | Python 3.11+ | solicitado; typing/async modernos |
| HTTP | httpx (async) | fan-out entre fontes |
| Agendamento | APScheduler | cron in-process, concorrência (Req 7) |
| Scraping | Playwright | solicitado; automação robusta (Req 2) |
| Validação | pydantic v2 | schema da KB + config (Req 3, 8) |
| Persistência | SQLAlchemy + SQLite/PG | paridade dev→prod (Req 10) |
| API | FastAPI | health/metrics/trigger (Req 9) |
| Telegram | Bot API via httpx | simples, sem dep pesada (Req 6) |
