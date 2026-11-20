# Requisitos — Backend de Milhas (módulo OPCIONAL)

> **Status: OPCIONAL.** Este é um módulo complementar, não o produto principal. O deliverable prioritário é o **Travel Hacking Toolkit** (plugins/skills para Claude Code, Codex e OpenCode), especificado em `.kiro/specs/travel-hacking-toolkit/`. Este backend é um serviço Python autônomo para quem quer **monitoramento contínuo + alertas automáticos** rodando sozinho, fora do fluxo interativo do agente.

## Introdução

Um serviço de backend em Python que monitora continuamente a **disponibilidade de assentos-prêmio (em milhas)**, cruza com uma base de **sweet spots** (tabelas fixas e parcerias estratégicas entre companhias), calcula o **valor matemático** de cada resgate (centavos por milha / CPM, milhas vs dinheiro) e **dispara alertas** quando surge uma oportunidade lucrativa (webhook n8n ou Telegram).

### Princípio free-first (herdado do toolkit)

Toda capacidade principal DEVE funcionar com **zero chaves pagas**:
- Disponibilidade-prêmio em cache (~60 dias) via MCP/Partner da seats.aero sem login é o caminho padrão.
- Busca ao vivo além de 60 dias e alertas da fonte PODEM exigir chave opcional (seats.aero Pro) e DEVEM degradar para o cache gratuito quando ausente.
- Tarifa em dinheiro usa fontes sem chave + Duffel (busca grátis).
- Scraping Playwright é **opt-in, desligado por padrão**, documentado como risco de ToS, nunca obrigatório.

### Escopo

- **No escopo:** motor de busca de disponibilidade, base alianças/milhas, calculadora CPM, detector de sweet spots, sistema de alertas (n8n/Telegram), agendamento, persistência, resiliência.
- **Fora do escopo (v1):** emissão/reserva real, dados de pagamento, frontend.
- **Reaproveita** os arquivos `data/*.json` do toolkit (alianças, sweet spots, transferências, valuations) para não duplicar conhecimento.

### Glossário

- **Assento-prêmio:** assento resgatável com milhas, cabine premium salvo indicação.
- **Sweet spot:** resgate de alto valor conhecido (taxa fixa + caminho de reserva via parceiro).
- **CPM:** centavos por milha = (preço em dinheiro − taxas do prêmio) ÷ milhas × 100.
- **Moeda transferível:** pontos bancários flexíveis (Amex MR, Chase UR, Bilt, Capital One, Citi TY).

---

## Requisitos

### Requisito 1 — Motor de busca de disponibilidade (API-licenciada primeiro)

**História:** Como usuário, quero que o sistema consulte disponibilidade-prêmio ao vivo e em cache em vários programas, para saber quais assentos estão realmente resgatáveis.

#### Critérios de aceitação
1. QUANDO um job roda para rota/datas configuradas ENTÃO o sistema DEVE consultar a seats.aero (cache e/ou bulk) e retornar registros normalizados.
2. ONDE a rota é marcada para verificação ao vivo E o programa suporta busca ao vivo ENTÃO o sistema DEVE fazer busca ao vivo e mesclar com o cache.
3. QUANDO um registro é retornado ENTÃO o sistema DEVE normalizá-lo para um schema canônico (origem, destino, data, programa, companhia operadora, cabine, custo em milhas, taxas em dinheiro, assentos, fonte, `last_seen`).
4. SE um campo obrigatório vier ausente ENTÃO o sistema DEVE marcá-lo como nulo/desconhecido em vez de descartar o registro.
5. QUANDO os dados forem mais antigos que o limite de frescor (padrão 24h) ENTÃO o sistema DEVE marcá-los como `stale`.
6. QUANDO a API retornar erro de auth/limite/5xx ENTÃO o sistema DEVE aplicar retry/backoff e NÃO DEVE derrubar os jobs de outras rotas.

### Requisito 2 — Fallback por automação de browser (Playwright, opt-in)

**História:** Como operador, quero um fallback de scraping para fontes sem API, mas sem rodar de forma imprudente nem tomar bloqueio.

#### Critérios de aceitação
1. ONDE um programa não tem cobertura por API licenciada E o operador habilitou explicitamente o scraping ENTÃO o sistema DEVE usar um coletor Playwright.
2. SE o scraping não foi habilitado para o programa ENTÃO o sistema NÃO DEVE raspá-lo (desligado por padrão).
3. QUANDO o coletor roda ENTÃO DEVE respeitar limite por domínio, teto de concorrência e pacing aleatório.
4. QUANDO o alvo retornar CAPTCHA/bloqueio/layout inesperado ENTÃO o coletor DEVE abortar, registrar o motivo e cair para o dado licenciado/cache (nunca retornar vazio como se fosse "sem disponibilidade").
5. QUANDO extrair dados ENTÃO DEVE emiti-los no mesmo schema canônico do Requisito 1.
6. O sistema DEVE isolar cada execução (contexto de browser separado, sem cookies compartilhados salvo config) e injetar credenciais via secret store, nunca no código.
7. A documentação DEVE expor o risco de ToS/bloqueio e exigir aceite explícito para habilitar um coletor.

### Requisito 3 — Base de alianças e milhas (tabelas fixas + parcerias)

**História:** Como usuário, quero uma camada estruturada de alianças, tabelas fixas e mapeamento de parceiros, para que o sistema conheça os caminhos de reserva.

#### Critérios de aceitação
1. O sistema DEVE manter dados das três alianças (Star Alliance, oneworld, SkyTeam): companhias, programas, hubs.
2. O sistema DEVE manter o mapa de qual programa emite em qual companhia, incluindo parcerias cross-alliance e bilaterais (ex.: Virgin Atlantic → ANA).
3. O sistema DEVE manter tabelas fixas conhecidas ("sweet spots") para programas nomeados (ex.: TAP Miles&Go, Iberia Plus, BA Executive Club) com rota/região, cabine, custo em milhas, sobretaxas e caminho de reserva.
4. O sistema DEVE manter razões de transferência das moedas transferíveis para programas aéreos/hoteleiros.
5. QUANDO um arquivo é carregado ENTÃO DEVE ser validado contra schema e, em falha, recusar iniciar (ou marcar degradado) indicando o registro problemático.
6. CADA dataset DEVE ter `last_updated` e limite de validade, com aviso em log quando vencido.
7. A base DEVE ser editável como arquivos versionados (JSON/YAML) sem mudança de código.

### Requisito 4 — Calculadora de valor (CPM / milhas vs dinheiro)

**História:** Como usuário, quero o valor real do prêmio vs dinheiro, para agir só em oportunidades matematicamente boas.

#### Critérios de aceitação
1. QUANDO há prêmio e tarifa paga comparável ENTÃO o sistema DEVE calcular CPM = (preço − taxas_do_prêmio) ÷ milhas × 100.
2. QUANDO calcular ENTÃO DEVE incluir todo custo em dinheiro do prêmio (taxas, sobretaxas de combustível, taxas da companhia).
3. QUANDO o CPM de um programa atingir o limite configurável (padrão = valuation "piso" do programa) ENTÃO DEVE rotular como **alto valor**.
4. QUANDO o único caminho às milhas for transferência ENTÃO DEVE verificar o caminho na base (Req 3.4) e calcular sobre as milhas efetivas pós-razão.
5. SE não houver tarifa comparável ENTÃO DEVE dar valor absoluto pela valuation de referência e marcar `preço_indisponível`.
6. QUANDO um sweet spot casar ENTÃO DEVE anotar o id e a taxa esperada e sinalizar desvio entre observado e esperado.
7. A calculadora DEVE ser função pura (sem I/O), determinística e testável.

### Requisito 5 — Casamento de sweet spots e detecção de oportunidade

#### Critérios de aceitação
1. QUANDO há disponibilidade normalizada ENTÃO o matcher DEVE cruzar com sweet spots + mapa de parceiros para saber quais programas emitem o assento.
2. QUANDO o assento for emitível por um programa que o usuário possui (saldo direto ou alcançável via transferência) ENTÃO DEVE marcar a oportunidade como **alcançável**.
3. QUANDO uma oportunidade for alcançável E de alto valor ENTÃO o sistema DEVE emitir um **evento de oportunidade** (itinerário, programa, caminho de reserva, CPM, custo em milhas, comparação, frescor).
4. SE a disponibilidade for `stale` ENTÃO o evento DEVE levar flag `precisa_verificar`.
5. O matcher DEVE deduplicar eventos (não reemitir a mesma oportunidade salvo mudança material).

### Requisito 6 — Alertas (webhook n8n + Telegram)

#### Critérios de aceitação
1. QUANDO um evento de oportunidade é emitido ENTÃO o sistema DEVE entregar por cada canal habilitado (n8n, Telegram ou ambos).
2. QUANDO enviar ao n8n ENTÃO DEVE fazer POST de JSON estável com chave de idempotência derivada da oportunidade.
3. QUANDO enviar ao Telegram ENTÃO DEVE formatar um resumo legível (rota, cabine, programa, milhas + taxas, CPM, frescor, caminho de reserva) via Bot API e chat id configurado.
4. SE um canal falhar ENTÃO DEVE repetir com backoff e NÃO bloquear o outro canal.
5. O sistema DEVE aplicar cooldown por oportunidade para não spammar.
6. O alerta NUNCA DEVE conter segredos (chaves, senhas, tokens).

### Requisito 7 — Configuração de monitoramento & agendamento

#### Critérios de aceitação
1. O sistema DEVE permitir jobs com: origem(ns), destino(s), data/intervalo, cabine(s), programas-alvo (ou "todos"), mínimo de assentos, limite de CPM, intervalo de polling.
2. QUANDO o agendamento dispara ENTÃO DEVE rodar o pipeline busca → match → valor → alerta.
3. O sistema DEVE rodar jobs concorrentemente até um teto de workers sem um job travar os demais.
4. QUANDO a configuração for inválida (aeroporto/programa desconhecido) ENTÃO DEVE rejeitá-la no carregamento com mensagem clara.
5. A configuração DEVE ser recarregável sem perder jobs em andamento quando viável.

### Requisito 8 — Setup, segredos e onboarding

#### Critérios de aceitação
1. O sistema DEVE ler todos os segredos (seats.aero, tarifa paga, token/chat Telegram, URL n8n, credenciais de scraper) de variáveis de ambiente/secret store, nunca do código.
2. O sistema DEVE trazer `.env.example` documentando cada variável, o que libera, se é obrigatória e onde obter.
3. QUANDO faltar um segredo de um recurso habilitado ENTÃO DEVE falhar rápido só naquele recurso, deixando os demais rodarem (degradação graciosa, free-first).
4. A documentação DEVE deixar claro o que roda sem chave, o que precisa de chave e o que precisa de credenciais (com risco de ToS).
5. O sistema NUNCA DEVE ecoar segredos em logs, alertas ou erros.

### Requisito 9 — Resiliência, rate limiting e observabilidade

#### Critérios de aceitação
1. QUANDO qualquer upstream retornar erro transitório ENTÃO DEVE repetir com backoff exponencial + jitter até um teto e então registrar falha estruturada.
2. O sistema DEVE respeitar limites por provedor (inclusive quotas da seats.aero) e enfileirar/adiar em vez de exceder.
3. O sistema DEVE emitir logs estruturados por etapa (busca, match, valor, alerta) com id de correlação por execução.
4. O sistema DEVE expor health/métricas (jobs rodados, oportunidades, alertas, erros por provedor).
5. SE um provedor estiver em falha sustentada ENTÃO DEVE abrir circuit breaker e seguir servindo os demais.

### Requisito 10 — Persistência & histórico

#### Critérios de aceitação
1. QUANDO buscar disponibilidade ENTÃO DEVE persistir snapshots normalizados com fonte e frescor.
2. QUANDO emitir uma oportunidade ENTÃO DEVE persistir com valor calculado, caminho de reserva e resultado de entrega por canal.
3. A persistência DEVE suportar a deduplicação e o cooldown (Req 5.5, 6.5).
4. O sistema DEVE suportar política de retenção configurável e expurgar snapshots fora da janela.

---

## Requisitos não-funcionais

- **Runtime:** Python 3.11+.
- **Free-first:** nenhuma chave paga é pré-requisito de capacidade principal.
- **Desempenho:** matcher/calculadora processam ≥1.000 registros por execução sem lentidão patológica.
- **Segurança:** segredos só do ambiente; nunca em log; credenciais de scraper isoladas e opt-in.
- **Manutenibilidade:** base de conhecimento em arquivos versionados e validados; calculadora pura e testada; fontes plugáveis atrás de interface comum.
- **Conformidade:** APIs licenciadas/gratuitas por padrão; scraping opt-in e documentado como risco de ToS.
