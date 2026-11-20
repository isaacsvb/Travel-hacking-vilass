# Design — Travel Hacking Toolkit (free-first)

## Overview

The toolkit is a bundle of **skills** (markdown capability files), **MCP server configs** (real-time tools), and **reference data** (JSON), installable as a plugin on Claude Code and Codex, and via clone on OpenCode. The agent answers trip questions by loading the right skills, calling MCP tools, cross-referencing reference data, and returning a math-backed recommendation.

The central design constraint is **free-first**: the toolkit must be fully useful with zero paid keys. The architecture achieves this by layering sources — keyless MCP servers form the always-on base, and optional keys are thin upgrades behind graceful fallbacks.

### Verified external facts (as of the research for this spec)

- **Claude Code plugin** = a directory with `.claude-plugin/plugin.json`; a **marketplace** = a git repo with `.claude-plugin/marketplace.json`. Only `name` is required in the manifest. ([code.claude.com](https://code.claude.com/docs/en/plugins/create), [plugin reference](https://code.claude.com/docs/en/plugins-reference))
- **Skills and MCP servers are portable** across Claude Code, Codex, and Cursor; **hooks are not** (per-tool). ([developertoolkit.ai](https://developertoolkit.ai/en/ecosystem/plugins/building-plugins/))
- **OpenCode** has no plugin format: MCP goes under the `mcp` key of `opencode.json`; instructions live in `AGENTS.md`. ([github-mcp-server install guide](https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-opencode.md))
- **seats.aero** keyless MCP serves ~60 days of cached award availability; Pro sign-in/key adds live search + alerts. **Duffel** search is free (key optional). **Kiwi Tequila** and **Amadeus Self-Service** are access-gated/sunsetting, so they are not relied on for the free path.

*(External source content rephrased for licensing compliance.)*

> These facts change. MCP configs and skill bodies are structured so a source can be swapped without reworking the toolkit.

---

## Source layering (how free-first is guaranteed)

```
┌──────────────────────────────────────────────────────────────────────┐
│ TIER 0 — KEYLESS BASE (always on, zero keys)                           │
│  Cash flights: Skiplagged, Kiwi (MCP)                                  │
│  Hotels:       Trivago (MCP)                                           │
│  Ferries:      Ferryhopper (MCP)                                       │
│  Stays:        Airbnb (MCP)                                            │
│  Awards:       seats.aero MCP — cached, ~60 days, no sign-in           │
│  Reference:    local JSON (alliances, sweet-spots, transfers, CPP)     │
└───────────────────────────────┬──────────────────────────────────────┘
                                 │  graceful upgrade (optional keys)
┌───────────────────────────────▼──────────────────────────────────────┐
│ TIER 1 — OPTIONAL UPGRADES (each has a Tier-0 fallback)                │
│  SEATS_AERO_API_KEY / Pro → live award search, >60 days, alerts        │
│  DUFFEL_API_KEY           → cleaner per-fare-class GDS cash pricing     │
│  AWARDWALLET_*            → auto-pull balances & status                 │
│  LITEAPI_API_KEY          → live hotel rates                           │
│  SERPAPI / RAPIDAPI / TRIPADVISOR → extra hotel/discovery sources       │
└───────────────────────────────┬──────────────────────────────────────┘
                                 │  opt-in, OFF by default, never required
┌───────────────────────────────▼──────────────────────────────────────┐
│ TIER 2 — BROWSER COLLECTORS (Playwright, opt-in, ToS-risky)            │
│  Southwest / airline sites / portals — only if operator enables them   │
└────────────────────────────────────────────────────────────────────── ┘
```

**Rule the agent follows:** always attempt Tier 0; use Tier 1 only when its key is present; never block on a missing key; Tier 2 only when explicitly enabled. The agent catches missing-credential errors and continues (never asks "do you have key X?" as a gate). This directly satisfies Req 1 and the free-first NFR.

---

## Repository layout

```
travel-hacking-toolkit/
├── .claude-plugin/
│   ├── plugin.json              # Claude Code manifest (install root) — Req 9.1
│   └── marketplace.json         # Claude Code marketplace catalog
├── .agents/
│   └── plugins/marketplace.json # Codex marketplace catalog — Req 9.2
├── plugins/travel-hacking-toolkit/
│   ├── .codex-plugin/plugin.json
│   ├── .mcp.json                # Codex MCP config (bundled)
│   └── skills -> ../../skills   # skill bundle for Codex
├── opencode.json                # OpenCode MCP config (auto-discovered) — Req 9.3
├── AGENTS.md -> CLAUDE.md       # OpenCode instructions (symlink)
├── CLAUDE.md                    # agent system prompt + routing (free-first rules)
├── .mcp.json                    # Claude Code MCP config — Req 9.4
├── .env.example                 # all optional keys documented — Req 10.2
├── agents/travel-hacker.md      # plugin subagent (synced from CLAUDE.md)
├── data/                        # reference knowledge base (Req 6)
│   ├── alliances.json
│   ├── partner-awards.json
│   ├── sweet-spots.json
│   ├── transfer-partners.json
│   └── points-valuations.json
├── skills/                      # capability files (Req 8)
│   ├── <orchestration>/SKILL.md # plan-trip, compare-flights, compare-hotels, trip-calculator, getting-started
│   ├── <flights>/SKILL.md       # seats-aero, duffel, skiplagged-notes, ...
│   ├── <hotels>/SKILL.md
│   ├── <loyalty>/SKILL.md       # awardwallet, transfer-partners, ...
│   └── <reference>/SKILL.md     # flight-search-strategy, points-valuations, partner-awards, alliances, sweet-spots, fallback-and-resilience
├── scripts/
│   ├── setup.sh / setup.ps1     # interactive installer (pick agent, keyless OK)
│   ├── setup-keys.sh / .ps1     # optional-key setup, masked input — Req 10.1
│   ├── gen-skill-tables.sh      # regenerate README/llms.txt tables — Req 12.3
│   └── smoke-test.sh            # validate frontmatter, MCP JSON, manifest — Req 12.4
├── llms.txt                     # machine-readable skill index — Req 12.3
└── README.md                    # free-first quick start + install — Req 12.1
```

OpenCode uses the clone; Claude Code/Codex use the plugin; contributors can run the plugin from the working tree with `--plugin-dir .` (Req 9.6).

---

## Components and interfaces

### MCP servers (Tier 0 keyless + Tier 1 optional)

Config lives in `.mcp.json` (Claude Code), `opencode.json` (OpenCode), and the Codex plugin's `.mcp.json`. Keyless servers have no auth block; optional ones read a key from the environment and are simply inert/skipped when it's unset.

| Server | Tier | Key | Capability |
|---|---|---|---|
| Skiplagged | 0 | none | cash flights, hidden-city |
| Kiwi | 0 | none | cash flights, virtual interlining |
| Trivago | 0 | none | hotel metasearch |
| Ferryhopper | 0 | none | ferries |
| Airbnb | 0 | none | stays |
| seats.aero | 0→1 | none (Pro optional) | awards cached ~60d; Pro adds live + alerts |
| Duffel | 1 | optional | per-fare-class GDS cash |
| LiteAPI | 1 | optional | live hotel rates |

### Skills (progressive disclosure, Req 8)

Each `SKILL.md` has frontmatter (`name`, `description`, `category`, `summary`, optional `api_key`) with **no colons/quotes/backticks in values** (cross-parser safety, Req 8.5), plus a body with usage, examples, and failure handling.

- **Orchestration** (`plan-trip`, `compare-flights`, `compare-hotels`, `trip-calculator`, `getting-started`): call individual source skills and assemble the answer.
- **Source** (`seats-aero`, `duffel`, hotel skills, `awardwallet`, ...): wrap a tool/API with concrete usage.
- **Reference** (`flight-search-strategy`, `points-valuations`, `partner-awards`, `alliances`, `sweet-spots`, `fallback-and-resilience`): institutional knowledge that auto-loads on relevant context and points at `data/` files rather than restating values (Req 6.5).

### Agent routing & free-first behavior (`CLAUDE.md` / `AGENTS.md`)

The system prompt encodes the free-first rules so the agent behaves correctly regardless of configured keys:

1. Attempt Tier 0 for every request; add Tier 1 only when the key is present; catch missing-credential errors and continue (Req 1.3, never gate on a key).
2. For a trip question: load `flight-search-strategy` + `fallback-and-resilience`, search cash (keyless) + awards (keyless cached, or Pro if keyed) in parallel, pull balances if AwardWallet keyed else ask once, gate award options against reachable programs, compute CPP, and present a ranked recommendation.
3. Show the CPP math; label redemptions good/mediocre/poor against `points-valuations.json` (Req 4.3).
4. At the end, mention at most **one** optional key that would have improved *this* result — only if relevant (Req 1.5).
5. Always note award-data freshness and advise verifying stale data before booking (Req 2.3).

### CPP / value logic (reference skill + data)

CPP is computed by the agent following `trip-calculator` + `points-valuations`, using `data/`:

```
CPP = (cash_price − award_cash_fees) / points × 100      (Req 4.1, 4.2)
effective_points(program) = direct + max ratio-adjusted transferable  (Req 5.3)
```

Transfer paths are verified in `transfer-partners.json` before any transfer recommendation (Req 4.4, 5.4); active transfer bonuses adjust the effective ratio (Req 4.5). When cash is unavailable, fall back to the program's reference valuation and mark the comparison incomplete (Req 4.6).

### Reference knowledge base (`data/`, Req 6)

Versioned JSON, each with `last_updated` + staleness threshold. Seeded from the reference project's structure: `alliances.json`, `partner-awards.json` (incl. cross-alliance like Virgin Atlantic→ANA), `sweet-spots.json` (TAP Miles&Go, Iberia Plus, BA Executive Club, etc.), `transfer-partners.json`, `points-valuations.json` (floor/ceiling per program). Editable without code changes (Req 6.4).

### Setup flow (`scripts/`, Req 10)

- `setup.sh` / `setup.ps1`: pick the agent (OpenCode / Claude Code / Codex / all), wire the plugin or clone config, pull nothing paid. Works fully keyless.
- `setup-keys.sh` / `.ps1`: prompt for each **optional** key with masked input, validate, write to shell rc with a backup, never echo. Keys stay out of scrollback and chat (Req 10.1, 10.4).
- `getting-started` skill: detect current setup, list which capabilities are already active keyless, point at the key script for upgrades, show sample prompts (Req 10.5).

---

## Free-first: how each "paid" concern is neutralized for personal use

This answers the user's direct question — "it uses a paid API, can I get around that? personal use only."

| Concern | Free path (default) | Optional paid upgrade | What you give up for free |
|---|---|---|---|
| **Award availability** | seats.aero **keyless MCP** — cached, ~60 days | seats.aero Pro (~$99/yr) → live search, >60 days, alerts | long-lead planning + instant alerts; cached 60-day search still works |
| **Cash fares** | Skiplagged + Kiwi MCP (keyless) | Duffel (free to search) / SerpAPI / RapidAPI | cleaner per-fare-class GDS pricing; keyless still returns fares |
| **Balances** | user types their balances once | AwardWallet (business tier) | auto-pull convenience; manual entry works fine |
| **Hotels** | Trivago + Airbnb (keyless) | LiteAPI / SerpAPI | live bookable rates; discovery still works keyless |
| **Airline-site award space** | not scraped by default | — | nothing core; scraping stays opt-in and ToS-risky |

**Net:** for personal use you can run the whole toolkit at **$0**. The only capability genuinely behind a paywall is *live* award search beyond 60 days plus alerts (seats.aero Pro). Everything else has a working keyless path. The toolkit is explicitly built so the paid key is an upgrade you opt into, not a gate.

---

## Data-capture bottlenecks (carried over, still relevant)

1. **"No results" ≠ "sold out".** A rate-limited/errored source must not look like no availability. The `fallback-and-resilience` skill makes the agent distinguish error from empty and continue with other sources (Req 2.5, 11.3).
2. **Staleness.** seats.aero cached data disappears before you can ticket. The agent always surfaces the cache timestamp and advises verifying stale data on the airline site (Req 2.3).
3. **Fee accuracy drives CPP.** Miss a fuel surcharge and a "great" redemption is actually mediocre; CPP always includes full award cash cost (Req 4.2).
4. **Chart devaluation.** Fixed award rates devalue often; `data/` files are versioned with staleness thresholds and the agent flags observed-vs-expected gaps (Req 6.2).
5. **Scraping is blocked & ToS-risky.** Kept opt-in, off by default, fail-loud, and never required for free-first (Req 11).
6. **Gated cash APIs.** Kiwi/Amadeus self-serve are sunsetting; the free path relies on keyless MCPs + Duffel, not on those (design note, Req 3.4).

---

## Error handling

| Failure | Behavior |
|---|---|
| Optional key absent | skip that Tier-1 source silently, use Tier-0 fallback (Req 1.3) |
| Award source 401/429/5xx | don't render as "no availability"; continue other sources (Req 2.5) |
| Stale award data | present with freshness note + verify-before-booking advice (Req 2.3) |
| No comparable cash fare | absolute valuation from reference data, mark incomplete (Req 4.6) |
| Transfer path not in data | do not recommend the transfer (Req 5.4) |
| Scraper blocked/CAPTCHA | abort target, fail loud, fall through (Req 11.3) |
| Secret missing for enabled feature | actionable message; other features keep working (free-first) |

## Testing strategy

- **Smoke test** (`smoke-test.sh`, Req 12.4): skill frontmatter valid (no colons/quotes in values), MCP config is valid JSON per agent, plugin manifest validates, docs skill tables match generated output.
- **Keyless-path test:** with no env keys set, assert the toolkit still routes cash/hotel/ferry/Airbnb + cached awards (Req 1).
- **Agent discovery test:** on a real trip question, the agent loads `flight-search-strategy` + `fallback-and-resilience` and does not gate on a missing key.
- **Data validation:** each `data/*.json` parses and carries `last_updated` within its staleness window.

## Technology choices

| Concern | Choice | Why |
|---|---|---|
| Capability format | Skills (`SKILL.md`) | portable across the 3 agents; progressive disclosure |
| Real-time tools | MCP servers | portable; keyless base enables free-first |
| Claude Code install | plugin + marketplace | one-command install (Req 9.1) |
| Codex install | plugin + marketplace catalog | parity with Claude Code (Req 9.2) |
| OpenCode install | clone + `opencode.json` + `AGENTS.md` | no plugin format exists (Req 9.3) |
| Reference data | versioned JSON | editable without code changes (Req 6) |
| Setup | shell scripts, masked key input | safe secret handling, keyless-first (Req 10) |
| Optional Python backend | separate Portuguese spec | monitoring/alerts service, not core |
