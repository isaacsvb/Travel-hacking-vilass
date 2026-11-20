# Requirements — Travel Hacking Toolkit (free-first)

## Introduction

A **travel hacking toolkit** that plugs into AI coding agents (Claude Code, Codex, OpenCode) so a user can ask natural-language questions like *"find me the best way to get a business-class flight to Tokyo with points, miles, or cash"* and get an opinionated, math-backed answer.

The toolkit ships **skills** (markdown capability files the agent loads on demand) and **MCP servers** (real-time tools the agent calls), plus reference data (alliances, sweet spots, transfer ratios, point valuations). It searches **award availability** and **cash fares**, compares them (cents-per-point), uses the user's loyalty balances when provided, and also covers hotels, ferries, and Airbnb. A setup flow makes adding API keys easy and safe.

### Design principle (binding): FREE-FIRST

Every core capability MUST work with **zero paid API keys**. Paid keys are strictly an **optional upgrade** that unlock extras, never a prerequisite. Concretely:

- Cash flight search, hotel/ferry/Airbnb search, and **cached award availability for ~the next 60 days** MUST work with no keys at all (free MCP servers + the keyless seats.aero MCP).
- **Award availability beyond ~60 days, live award search, and alerts** MAY require an optional key (seats.aero Pro) and MUST degrade gracefully to the free cached path when the key is absent.
- Auto-pulling loyalty balances MAY require an optional key (AwardWallet) and MUST fall back to **user-supplied balances** when absent.
- Browser-automation collectors (Playwright) are **opt-in, off by default**, documented as Terms-of-Service-risky, and never required for a core capability.

The agent MUST NOT ask "do you have key X?" as a gate before trying a tool. It tries whatever is available, catches missing-credential errors, and continues. See design.

### Install model

- **Plugin install (no clone):** Claude Code and Codex install the toolkit as a packaged plugin from a marketplace.
- **Clone install (contributors + OpenCode):** OpenCode has no plugin format, so OpenCode users and contributors clone the repo and the config is auto-discovered.

### Scope

- **In scope (v1):** skills + MCP config + reference data + setup flow + docs, free-first, for the three agents; flight (award + cash) comparison, hotels, ferries, Airbnb, loyalty/transfer logic, CPP calculation.
- **Optional module:** a standalone **Python backend service** (scheduler + award-availability monitor + CPM calculator + n8n/Telegram alerts), specified separately in Portuguese under `.kiro/specs/backend-milhas/` — not part of the core toolkit deliverable.
- **Out of scope:** actually booking/ticketing, storing payment data, a web/mobile frontend.

### Glossary

- **Skill:** a `SKILL.md` file (name + description always loaded; body loaded on demand) giving the agent a capability.
- **MCP server:** a Model Context Protocol server exposing callable tools to the agent.
- **Award / premium seat:** a seat bookable with miles/points, premium cabin unless stated.
- **Sweet spot:** a known high-value redemption (fixed rate + partner booking path).
- **CPP / CPM:** cents per point (per mile) = (cash price − award cash fees) ÷ points × 100.
- **Transferable currency:** flexible bank points (Amex MR, Chase UR, Bilt, Capital One, Citi TY).

---

## Requirements

### Requirement 1 — Zero-key core capability (free-first guarantee)

**User story:** As a user who hasn't configured anything, I want the toolkit to still do useful travel search immediately, so that I can get value before paying for or signing up for anything.

#### Acceptance criteria

1. WHEN the toolkit is installed with no API keys set THEN cash flight search, hotel search, ferry search, and Airbnb search SHALL work via keyless MCP servers.
2. WHEN the toolkit is installed with no API keys set THEN cached award availability for approximately the next 60 days SHALL work via the keyless seats.aero MCP.
3. WHEN a capability requires an optional key that is absent THEN the toolkit SHALL fall back to the best keyless path AND SHALL complete the request rather than failing.
4. THE toolkit SHALL NOT make any paid key a prerequisite for a core capability.
5. WHEN a search completes using only free sources AND an optional key would have materially improved THIS specific result THEN the agent SHALL mention that one key in a single closing line (not a list, only when relevant).

### Requirement 2 — Award availability search (free cached + optional paid upgrade)

**User story:** As a travel hacker, I want to search premium-award availability across many mileage programs, so that I know which seats are bookable with points.

#### Acceptance criteria

1. WHEN the user asks about award availability within ~60 days THEN the toolkit SHALL return results via the keyless seats.aero MCP (cached).
2. WHERE `SEATS_AERO_API_KEY` (or a Pro MCP sign-in) is configured THEN the toolkit SHALL additionally support live search, dates beyond the cached window, and alerts.
3. WHEN award data is returned THEN the agent SHALL note data freshness (cache timestamp) AND SHALL advise verifying on the airline site before booking when data is stale (≥24h).
4. WHEN searching for multiple travelers THEN the toolkit SHALL search for the requested seat count rather than assuming 1 seat guarantees N.
5. IF the award source errors or is rate-limited THEN the toolkit SHALL not present an error as "no availability" and SHALL continue with other sources.

### Requirement 3 — Cash fare search (keyless + optional richer sources)

**User story:** As a user, I want cash flight prices alongside award options, so that I can compare points vs money.

#### Acceptance criteria

1. WHEN the user asks for flights THEN the toolkit SHALL return cash fares via keyless MCP servers (e.g. Skiplagged, Kiwi).
2. WHERE an optional cash key is configured (e.g. Duffel — free to search) THEN the toolkit SHALL add cleaner per-fare-class GDS pricing.
3. WHEN multiple cash sources return results THEN the toolkit SHALL merge and present them in a single comparison, de-emphasizing duplicates.
4. WHEN a cash source requires a key that is absent THEN the toolkit SHALL skip it silently and use keyless sources.

### Requirement 4 — Points vs cash comparison (CPP, math-backed)

**User story:** As a travel hacker, I want the toolkit to compute the real value of points vs cash, so that I act only on high-value redemptions and don't waste points.

#### Acceptance criteria

1. WHEN an award option and a comparable cash fare exist THEN the toolkit SHALL compute CPP = (cash_price − award_cash_fees) ÷ points × 100 and show the math.
2. WHEN computing CPP THEN the toolkit SHALL include all out-of-pocket award costs (taxes, fuel surcharges, carrier fees).
3. WHEN evaluating a redemption THEN the toolkit SHALL compare CPP against the program's floor/ceiling valuation and label it good / mediocre / poor.
4. WHEN the only path to the points is a transfer from a bank currency THEN the toolkit SHALL verify a transfer path exists in the reference data and compute effective points after the transfer ratio.
5. WHEN a current transfer bonus applies THEN the toolkit SHALL factor the effective ratio into the recommendation.
6. IF no comparable cash fare is available THEN the toolkit SHALL still give an absolute valuation using reference data and mark the comparison incomplete.

### Requirement 5 — Loyalty balances & reachability

**User story:** As a user, I want recommendations matched to the points I actually have (or can transfer in), so that the advice is actionable for me.

#### Acceptance criteria

1. WHERE `AWARDWALLET_API_KEY` and `AWARDWALLET_USER_ID` are configured THEN the toolkit SHALL auto-pull balances and elite status without asking.
2. IF AwardWallet is not configured THEN the toolkit SHALL ask the user once for their balances OR proceed with advice that doesn't depend on exact balances.
3. WHEN the user holds a transferable currency THEN the toolkit SHALL compute an effective balance per program = direct balance + maximum ratio-adjusted transferable amount, and SHALL NOT dismiss a program whose direct balance is zero but is reachable by transfer.
4. WHEN recommending a transfer THEN the toolkit SHALL verify the transfer path exists in the reference data before committing.

### Requirement 6 — Reference knowledge base (alliances, sweet spots, transfers, valuations)

**User story:** As a travel hacker, I want the toolkit to know alliance structures, fixed award charts, partner-booking paths, transfer ratios, and point valuations, so that it reasons correctly instead of guessing.

#### Acceptance criteria

1. THE toolkit SHALL ship versioned data files for: alliances, partner-award mappings (incl. cross-alliance/bilateral), sweet spots, transfer-partner ratios, and point valuations (floor/ceiling).
2. EACH data file SHALL carry a `last_updated` date and a staleness threshold.
3. THE sweet-spot data SHALL include named fixed-chart programs (e.g. TAP Miles&Go, Iberia Plus, BA Executive Club) with route/region, cabin, points cost, surcharges, and booking path.
4. THE data SHALL be editable without a code change so rates can be updated as programs devalue.
5. WHEN a skill relies on a data file THEN it SHALL reference that file rather than hard-coding values in prose.

### Requirement 7 — Broader travel search (hotels, ferries, Airbnb)

**User story:** As a user, I want hotels, ferries, and Airbnb search in the same toolkit, so that I can plan a whole trip in one place.

#### Acceptance criteria

1. THE toolkit SHALL provide keyless hotel metasearch, ferry search, and Airbnb search via MCP servers.
2. WHEN hotel results include branded chain properties THEN the toolkit SHALL map them to their loyalty program and compare points vs cash for the stay.
3. WHERE an optional hotel key is configured (e.g. LiteAPI) THEN the toolkit SHALL add live hotel rates; absent the key, keyless hotel discovery SHALL still work.
4. THE toolkit SHALL present flight and hotel results as markdown tables with a clear recommendation after the table.

### Requirement 8 — Skills architecture (progressive disclosure)

**User story:** As a contributor, I want capabilities expressed as discoverable skills, so that the toolkit grows without bloating the agent's always-on context.

#### Acceptance criteria

1. EACH skill SHALL be a `SKILL.md` with frontmatter (`name`, `description`, `category`, `summary`, optional `api_key`) and a body with usage, examples, and failure handling.
2. THE agent SHALL load only skill names + descriptions at session start, and the full body only when it decides to use the skill.
3. THE toolkit SHALL provide orchestration skills (e.g. plan-trip, compare-flights, compare-hotels, trip-calculator) that call individual source skills.
4. THE toolkit SHALL provide reference skills (flight-search-strategy, points-valuations, partner-awards, alliances, sweet-spots, fallback-and-resilience) that auto-load on relevant context.
5. SKILL frontmatter values SHALL avoid characters that break parsers (no colons/quotes/backticks in values), for cross-agent compatibility.

### Requirement 9 — Multi-agent install (plugin + clone), free by default

**User story:** As a user on any of the three agents, I want a one-command install that works, so that I don't have to wire things up manually.

#### Acceptance criteria

1. THE toolkit SHALL ship a Claude Code plugin (`.claude-plugin/plugin.json`) and a marketplace catalog (`.claude-plugin/marketplace.json`).
2. THE toolkit SHALL ship Codex plugin/marketplace config so Codex installs the same bundle.
3. FOR OpenCode (no plugin format) THE toolkit SHALL support the clone path with auto-discovered config (`opencode.json` for MCP, `AGENTS.md` for instructions).
4. THE MCP config SHALL be provided per agent (`.mcp.json` for Claude Code, `opencode.json` for OpenCode, bundled config for the Codex plugin).
5. WHEN installed with no keys THEN all keyless MCP servers SHALL be active immediately (Req 1).
6. THE toolkit SHALL support loading the plugin from a local working tree for contributors (e.g. `claude --plugin-dir .`).

### Requirement 10 — Setup flow & safe secret handling

**User story:** As a new user, I want adding API keys to be easy and safe, so that I can unlock extras without leaking secrets.

#### Acceptance criteria

1. THE toolkit SHALL provide a setup script that prompts for each optional key with masked input, validates it, writes it to the shell rc with a backup, and never echoes the value.
2. THE toolkit SHALL ship an `.env.example` documenting every supported variable, which feature it unlocks, whether it is required (all optional in free-first), and where to obtain it.
3. THE setup docs SHALL clearly state which capabilities work with zero keys, which need an optional key, and which need account credentials (with the ToS risk).
4. THE toolkit SHALL read keys from the environment and SHALL never commit secrets or echo them into logs, chat, or alerts.
5. A getting-started skill SHALL detect current setup, point to the setup script for missing keys, and show sample prompts.

### Requirement 11 — Browser-automation collectors (opt-in, never required)

**User story:** As a power user, I want optional browser automation for sites with no API, but I never want it required or running by default.

#### Acceptance criteria

1. THE toolkit SHALL keep all Playwright/browser collectors opt-in and OFF by default.
2. NO core capability SHALL depend on a browser collector (free-first is satisfied without any scraping).
3. WHEN a collector runs THEN it SHALL respect rate limits, isolate sessions, and fail loud on block/CAPTCHA (never present a block as "no availability").
4. THE docs SHALL state the ToS and account/IP-ban risk and require explicit opt-in to enable a collector.

### Requirement 12 — Documentation & polish

**User story:** As a user, I want clear docs and a polished feel, so that the toolkit is ready to use.

#### Acceptance criteria

1. THE README SHALL cover: what it does, free-first quick start (zero keys), plugin install per agent, clone path, the optional-key table (what each unlocks + cost), and example prompts.
2. THE docs SHALL make the free-first guarantee explicit and show the single highest-value optional key (seats.aero Pro) framed as optional.
3. THE toolkit SHALL include an `llms.txt` / machine-readable index of skills.
4. THE repo SHALL include a smoke test that validates skill frontmatter, MCP config JSON, and plugin manifest.

---

## Non-functional requirements

- **Free-first:** no paid key is ever required for a core capability (Req 1). This is the top non-functional constraint.
- **Portability:** skills and MCP config work across Claude Code, Codex, and OpenCode; per-agent differences (plugin vs clone, hooks) are isolated.
- **Security:** secrets only from the environment; never committed, logged, or echoed; scraper credentials isolated and opt-in.
- **Graceful degradation:** every optional dependency has a keyless fallback; the agent never gates on a key before trying.
- **Maintainability:** reference data is file-based and versioned; skill tables in docs are generated, not hand-edited.
- **Compliance:** licensed/free APIs are the default; scraping is opt-in and documented as ToS-risky.
