# Plano de implementação — Backend de Milhas (módulo OPCIONAL)

> **Status: OPCIONAL.** Só implementar depois (ou em paralelo) ao Travel Hacking Toolkit (`.kiro/specs/travel-hacking-toolkit/`), que é o deliverable principal. Este backend reaproveita os arquivos `data/*.json` do toolkit.

Um **grafo de tarefas** para execução paralela. Após o scaffold, as lanes A–E rodam concorrentes; pontos de junção explícitos por tarefa. **Free-first é regra transversal: nenhuma tarefa pode tornar uma chave paga pré-requisito de capacidade principal.**

## Grafo de execução

```
                         ┌─────────────┐
                         │ 0. Scaffold │
                         └──────┬──────┘
          ┌───────────────┬─────┴───────┬────────────────┬───────────────┐
          ▼               ▼             ▼                ▼               ▼
     LANE A          LANE B        LANE C           LANE D          LANE E
     domínio +       knowledge     infra            sources         alertas
     calculadora     (schemas)     (resiliência     (adaptadores    (n8n +
     (puro)                        + persist.)      + scrapers)     telegram)
          │ (A,B)        │              │ (C,D)         │               │
          └──────┬───────┘              └──────┬────────┘               │
                 ▼                              ▼                        │
             LANE F  (matcher)         (sources ligados à infra)         │
                 └──────────────┬───────────────────────┬──────────────┘
                                ▼                        ▼
                            LANE G                   LANE H
                            pipeline +               scheduler/config
                            orquestração             + api server
                                ▼
                            LANE I
                            e2e + docs + setup
```

Lanes **A, B, C, D, E em paralelo** após a tarefa 0.

---

## Tarefa 0 — Scaffold (bloqueante)

- [ ] 0. Scaffold do projeto
  - Criar layout (`backend_milhas/` com `app/`, `sources/`, `knowledge/`, `domain/`, `alerts/`, `infra/`, `api/`), `pyproject.toml` (Python 3.11+, httpx, pydantic v2, APScheduler, SQLAlchemy, playwright, pytest, respx/pytest-asyncio), lint/format, `__init__.py`.
  - `.env.example` stub (preenchido na Lane I) e `README.md` esqueleto.
  - _Deps: nenhuma_ · _Requisitos: NFR (runtime, manutenibilidade)_

---

## Lane A — Domínio & calculadora  *(paralelo)*

- [ ] A1. Modelos canônicos
  - `domain/models.py`: `Cabin`, `Money`, `Availability` (com `is_stale`), `BookingPath`, `Opportunity`, `AvailabilityQuery`, `MonitorJob`. Nulos explícitos.
  - _Deps: 0_ · _Requisitos: 1.3, 1.4, 1.5_

- [ ] A2. Calculadora pura + testes
  - `domain/calculator.py`: `compute_cpm`, `classify_value`, `effective_miles`, desvio de sweet spot, `preço_indisponível`. Sem I/O. Testes exaustivos.
  - _Deps: A1_ · _Requisitos: 4.1–4.7_

---

## Lane B — Base de conhecimento  *(paralelo)*

- [ ] B1. Schemas dos datasets
  - `knowledge/schemas.py` (pydantic) para alliances, partner-awards, sweet-spots, transfer-partners, points-valuations; cada um com `last_updated` + validade.
  - _Deps: 0_ · _Requisitos: 3.1–3.4, 3.6_

- [ ] B2. Loader com validação + validade
  - `knowledge/loader.py`: carrega/valida arquivos `data/*.json` (reusados do toolkit), falha/degrada apontando o registro, avisa quando vencido.
  - _Deps: B1_ · _Requisitos: 3.5, 3.6, 3.7_

---

## Lane C — Infra: resiliência & persistência  *(paralelo)*

- [ ] C1. Primitivas de resiliência
  - `infra/resilience.py`: retry/backoff+jitter, token-bucket por provedor, circuit breaker. Testes com injeção de falha.
  - _Deps: 0_ · _Requisitos: 9.1, 9.2, 9.5_

- [ ] C2. Logging estruturado
  - `infra/logging.py`: logs + id de correlação; filtro de scrub de segredos.
  - _Deps: 0_ · _Requisitos: 9.3, 8.5_

- [ ] C3. Persistência
  - `infra/persistence.py`: modelos SQLAlchemy (`availability_snapshots`, `opportunities`, `alert_log`), queries de dedup/cooldown, expurgo por retenção. SQLite dev + PG prod.
  - _Deps: 0_ (usa modelos de A1 quando disponíveis) · _Requisitos: 10.1–10.4_

---

## Lane D — Adaptadores de fonte & scrapers  *(paralelo)*

- [ ] D1. Protocolos + agregador
  - `sources/base.py` + agregador (fan-out, merge por chave, prefere mais fresco não-stale, mantém stale sinalizado, separa erro de vazio).
  - _Deps: A1_ · _Requisitos: 1.3, 1.6, 2.4_

- [ ] D2. Adaptador seats.aero (primário)
  - `sources/seats_aero.py`: cached/bulk/live; mapeia para `Availability`; respeita quotas via C1. Testes com fixtures.
  - _Deps: D1, C1_ · _Requisitos: 1.1–1.5, 9.2_

- [ ] D3. Adaptador Duffel (cash)
  - `sources/duffel.py`: tarifas pagas comparáveis para o CPM. Testes com fixtures.
  - _Deps: D1, C1_ · _Requisitos: 4.1, 4.5_

- [ ] D4. Base do coletor Playwright (opt-in, seguro)
  - `sources/scrapers/base.py`: desligado por padrão, pacing/jitter/concorrência (via C1), isolamento de contexto, credenciais injetáveis, falha-alto (`ScrapeBlocked`/`ScrapeLayoutChanged`). Testes com snapshots incl. página de bloqueio.
  - _Deps: D1, C1_ · _Requisitos: 2.1–2.6_

- [ ] D5. Um scraper de referência
  - Um `sources/scrapers/<programa>.py` concreto como padrão; emite `Availability(source="scraper:<prog>")`.
  - _Deps: D4_ · _Requisitos: 2.1, 2.5_

---

## Lane E — Canais de alerta  *(paralelo)*

- [ ] E1. Protocolo + webhook n8n
  - `alerts/base.py` e `alerts/n8n.py`: POST JSON estável com idempotência, retry+backoff, payload sem segredos.
  - _Deps: A1, C1_ · _Requisitos: 6.1, 6.2, 6.4, 6.6_

- [ ] E2. Canal Telegram
  - `alerts/telegram.py`: Bot API, resumo legível, chat id configurado, retry+backoff, independente do n8n.
  - _Deps: A1, C1_ · _Requisitos: 6.1, 6.3, 6.4, 6.6_

---

## Lane F — Matcher  *(junção de A + B)*

- [ ] F1. Matcher de sweet spot & alcançabilidade
  - `domain/matcher.py`: cruza disponibilidade com partner-awards + sweet-spots; alcançabilidade por saldo + transferências; `dedup_key`; emite `Opportunity` só quando alcançável E alto valor; `needs_verification` em stale. Testes sobre fixtures da KB.
  - _Deps: A1, A2, B2_ · _Requisitos: 5.1–5.4_

---

## Lane G — Orquestração do pipeline  *(junção de C, D, E, F)*

- [ ] G1. Orquestrador do pipeline
  - `app/pipeline.py`: busca (agregador) → match → valor → dedup/cooldown (persistência) → alerta; id de correlação; uma etapa/fonte com falha não derruba a execução.
  - _Deps: D1, D2, D3, F1, A2, C2, C3, E1, E2_ · _Requisitos: 5.5, 6.5, 9.3, 1.6_

---

## Lane H — Scheduler, config, API  *(junção com G)*

- [ ] H1. Config & segredos
  - `app/config.py`: carrega jobs + settings; segredos do ambiente; valida (rejeita aeroporto/programa desconhecido); falha-rápido por recurso com degradação graciosa.
  - _Deps: 0, B2_ · _Requisitos: 7.1, 7.4, 8.1, 8.3, 8.5_

- [ ] H2. Scheduler & concorrência
  - `app/scheduler.py`: agenda jobs, workers concorrentes com teto, sem um job travar outros, config recarregável.
  - _Deps: H1, G1_ · _Requisitos: 7.2, 7.3, 7.5_

- [ ] H3. API opcional (health/metrics/trigger)
  - `api/server.py` (FastAPI): `/health`, `/metrics`, trigger manual.
  - _Deps: G1, C3_ · _Requisitos: 9.4_

---

## Lane I — E2E, setup, docs  *(junção final)*

- [ ] I1. Testes de integração ponta a ponta
  - Pipeline completo sobre fixtures com n8n/Telegram mockados: oportunidades, dedup/cooldown, stale→needs_verification, payloads sem segredos.
  - _Deps: G1, H2_ · _Requisitos: todos do pipeline; NFR testabilidade_

- [ ] I2. Setup & `.env.example`
  - `.env.example` completo (cada var, o que libera, obrigatória?, onde obter) e doc de setup cobrindo capacidades sem chave vs com chave vs credenciais.
  - _Deps: H1_ · _Requisitos: 8.1–8.4_

- [ ] I3. Documentação & aviso de conformidade
  - README: arquitetura, quick start, quais recursos precisam de qual chave, e o risco explícito de ToS/bloqueio do scraping + aceite do operador para habilitar coletor.
  - _Deps: I2, D4_ · _Requisitos: 2.7, 8.4; NFR conformidade_

---

## Atribuição paralela sugerida (5 agentes)

| Agente | Lanes após a tarefa 0 |
|---|---|
| Agente 1 | A (modelos + calculadora) → F (matcher) |
| Agente 2 | B (base de conhecimento) → auxilia F |
| Agente 3 | C (infra: resiliência + persistência) |
| Agente 4 | D (fontes + scrapers) |
| Agente 5 | E (alertas) → integração G/H/I |

Junções: **F** precisa de A+B; **G** precisa de C+D+E+F; **H** precisa de G; **I** precisa de G+H.
