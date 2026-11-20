# Implementation Plan — Travel Hacking Toolkit (free-first)

A **task graph** built for parallel agent execution. After the scaffold, lanes A–F run concurrently; merge points are explicit per task. Every task lists dependencies and the requirements it satisfies. **Free-first is a cross-cutting acceptance gate: no task may introduce a paid key as a prerequisite for a core capability.**

## Execution graph

```
                         ┌─────────────┐
                         │ 0. Scaffold │
                         └──────┬──────┘
      ┌──────────────┬──────────┼───────────┬───────────────┬─────────────┐
      ▼              ▼          ▼           ▼               ▼             ▼
 ┌─────────┐  ┌───────────┐ ┌─────────┐ ┌──────────┐ ┌────────────┐ ┌──────────┐
 │ LANE A  │  │ LANE B    │ │ LANE C  │ │ LANE D   │ │ LANE E     │ │ LANE F   │
 │ MCP     │  │ reference │ │ source  │ │ reference│ │ orchestr.  │ │ install  │
 │ configs │  │ data/     │ │ skills  │ │ skills   │ │ skills     │ │ plugin + │
 │ keyless │  │ JSON (KB) │ │ (tools) │ │ (knowl.) │ │ + routing  │ │ clone    │
 │ base    │  │           │ │         │ │          │ │ CLAUDE.md  │ │ configs  │
 └────┬────┘  └─────┬─────┘ └────┬────┘ └────┬─────┘ └─────┬──────┘ └────┬─────┘
      │ (A)         │ (B)        │ (A,B)      │ (B)         │(C,D)        │(A)
      └─────────────┴────────────┴──────┬─────┴─────────────┴─────────────┘
                                         ▼
                                 ┌───────────────┐
                                 │ LANE G         │
                                 │ setup + docs + │
                                 │ smoke test     │
                                 └───────────────┘
```

---

## Task 0 — Scaffold (blocking)

- [ ] 0. Repo scaffold
  - Create the directory layout (`.claude-plugin/`, `.agents/`, `plugins/`, `skills/`, `data/`, `scripts/`, `agents/`), empty `CLAUDE.md`, `AGENTS.md -> CLAUDE.md` symlink, `.env.example` stub, `README.md` skeleton, `llms.txt` stub.
  - _Deps: none_ · _Requirements: 8, 9, NFR portability_

---

## Lane A — Keyless MCP base (free-first foundation)  *(parallel)*

- [ ] A1. Keyless MCP config (per agent)
  - Add Tier-0 keyless servers (Skiplagged, Kiwi, Trivago, Ferryhopper, Airbnb, seats.aero) to `.mcp.json` (Claude Code), `opencode.json` (OpenCode), and the Codex plugin `.mcp.json`. No auth blocks.
  - _Deps: 0_ · _Requirements: 1.1, 1.2, 7.1, 9.4, 9.5_

- [ ] A2. Optional MCP upgrades (inert without key)
  - Add Tier-1 optional servers (Duffel, LiteAPI) reading keys from env; ensure they are skipped/inert when the key is unset and never break the keyless base.
  - _Deps: A1_ · _Requirements: 1.3, 1.4, 2.2, 3.2, 7.3_

---

## Lane B — Reference knowledge base  *(parallel)*

- [ ] B1. Data schemas & seed files
  - Create `data/alliances.json`, `partner-awards.json` (incl. cross-alliance/bilateral), `sweet-spots.json` (TAP Miles&Go, Iberia Plus, BA Executive Club, etc.), `transfer-partners.json`, `points-valuations.json` (floor/ceiling). Each carries `last_updated` + staleness threshold.
  - _Deps: 0_ · _Requirements: 6.1, 6.2, 6.3_

- [ ] B2. Data validation in smoke test hook
  - Provide a validator (used by Lane G) that each file parses, has `last_updated`, and is within staleness; editable without code changes.
  - _Deps: B1_ · _Requirements: 6.2, 6.4, 12.4_

---

## Lane C — Source (tool) skills  *(parallel; needs A+B for examples)*

- [ ] C1. Award + cash source skills
  - `seats-aero` (keyless cached ~60d + optional Pro live/alerts), `duffel` (optional cash), plus notes skills for keyless cash (Skiplagged/Kiwi). Each documents keyless behavior and the optional upgrade, with failure handling (error ≠ "no availability").
  - _Deps: A1, A2, B1_ · _Requirements: 2.1, 2.2, 2.3, 2.5, 3.1, 3.2, 8.1, 8.5_

- [ ] C2. Hotel / ferry / stay source skills
  - Keyless hotel/ferry/Airbnb skills; optional LiteAPI skill; chain→loyalty mapping that triggers points-vs-cash for branded properties.
  - _Deps: A1, B1_ · _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] C3. Loyalty skills
  - `awardwallet` (auto-pull when keyed; else ask once), `transfer-partners` (cheapest path, effective balance incl. transfers).
  - _Deps: A1, B1_ · _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] C4. Browser-collector skill (opt-in template)
  - One opt-in Playwright collector skill as the pattern: OFF by default, rate-limited, isolated, fail-loud, ToS warning. Not required by any core path.
  - _Deps: A1_ · _Requirements: 11.1, 11.2, 11.3, 11.4_

---

## Lane D — Reference (knowledge) skills  *(parallel; needs B)*

- [ ] D1. Strategy & valuation skills
  - `flight-search-strategy` (canonical parallel search, source priority, free-first order), `points-valuations` (CPP formula, floor/ceiling, reference `data/`), `trip-calculator` inputs.
  - _Deps: B1_ · _Requirements: 4.1, 4.2, 4.3, 6.5, 8.4_

- [ ] D2. Partnership & resilience skills
  - `partner-awards`, `alliances`, `sweet-spots`, `fallback-and-resilience` (per-tool recovery, error-vs-empty). All point at `data/` files, no hard-coded values in prose.
  - _Deps: B1_ · _Requirements: 4.4, 5.3, 6.5, 8.4, 11.3_

---

## Lane E — Orchestration skills & agent routing  *(merge of C+D)*

- [ ] E1. Orchestration skills
  - `plan-trip` (hero), `compare-flights`, `compare-hotels`, `trip-calculator`, `getting-started`. They call source skills, assemble markdown tables + ranked recommendation, and show CPP math.
  - _Deps: C1, C2, C3, D1, D2_ · _Requirements: 4.1, 4.3, 4.5, 4.6, 5.3, 7.4, 8.3, 10.5_

- [ ] E2. CLAUDE.md agent routing (free-first rules)
  - Write `CLAUDE.md` (and the `travel-hacker` subagent, synced): Tier-0-always / Tier-1-if-keyed / never-gate-on-key, catch missing-credential errors, mention ≤1 relevant optional key at the end, always note freshness.
  - _Deps: E1_ · _Requirements: 1.3, 1.5, 2.3, 8.2_

---

## Lane F — Install configs (plugin + clone)  *(parallel; needs A)*

- [ ] F1. Claude Code plugin + marketplace
  - `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`; load from working tree with `--plugin-dir .` for contributors.
  - _Deps: A1_ · _Requirements: 9.1, 9.6_

- [ ] F2. Codex plugin + marketplace
  - `.agents/plugins/marketplace.json` + `plugins/travel-hacking-toolkit/.codex-plugin/plugin.json` + bundled `.mcp.json` + skills bundle.
  - _Deps: A1_ · _Requirements: 9.2, 9.4_

- [ ] F3. OpenCode clone config
  - `opencode.json` (MCP auto-discovery) + `AGENTS.md -> CLAUDE.md`; verify keyless servers active on clone.
  - _Deps: A1_ · _Requirements: 9.3, 9.5_

---

## Lane G — Setup, docs, smoke test  *(final merge)*

- [ ] G1. Setup scripts (keyless-first, safe keys)
  - `setup.sh`/`setup.ps1` (pick agent, wire plugin/clone, works fully keyless) and `setup-keys.sh`/`.ps1` (masked input, validate, backup rc, never echo).
  - _Deps: F1, F2, F3, E2_ · _Requirements: 10.1, 10.3, 10.4_

- [ ] G2. `.env.example` + getting-started wiring
  - Document every optional key (feature unlocked, optional, where to get it, cost). Ensure `getting-started` detects setup and signposts the key script.
  - _Deps: G1_ · _Requirements: 10.2, 10.3, 10.5_

- [ ] G3. README + llms.txt (free-first framing)
  - README: what it does, **zero-key quick start**, plugin install per agent, clone path, optional-key table (unlock + cost), example prompts; make the free-first guarantee explicit and frame seats.aero Pro as the one optional upgrade. Generate skill tables.
  - _Deps: G2, E1_ · _Requirements: 12.1, 12.2, 12.3_

- [ ] G4. Smoke test
  - Validate skill frontmatter (no colons/quotes in values), MCP config JSON per agent, plugin manifest, data files (Lane B2), and the **keyless-path assertion** (toolkit routes cash/hotel/ferry/Airbnb + cached awards with no keys).
  - _Deps: G3, B2_ · _Requirements: 1 (keyless), 8.5, 12.4_

---

## Optional module (not part of core deliverable)

- [ ] OPT. Python monitoring backend (Portuguese spec)
  - Implement per `.kiro/specs/backend-milhas/` — scheduler + award monitor + CPM calculator + n8n/Telegram alerts. Independent of the toolkit; can reuse `data/` files.
  - _Deps: B1 (shared data, optional)_ · _Requirements: tracked in the separate Portuguese spec_

---

## Suggested parallel assignment (6 agents)

| Agent | Lanes after task 0 |
|---|---|
| Agent 1 | A (keyless MCP base) → F (install configs) |
| Agent 2 | B (reference data) → B2 validator |
| Agent 3 | C (source skills) |
| Agent 4 | D (reference skills) |
| Agent 5 | E (orchestration + routing) — starts once C/D land |
| Agent 6 | G (setup/docs/smoke) — final merge |

Merge points: **E** needs C+D; **G** needs E+F (+B2). Free-first gate (G4 keyless assertion) must pass before release.
