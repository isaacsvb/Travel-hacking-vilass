# Travel Hacking Toolkit

AI-powered travel hacking with points, miles, and award flights. Drop-in skills and MCP servers for [Claude Code](https://code.claude.com), [Codex](https://openai.com/codex/), and [OpenCode](https://opencode.ai).

Ask your AI to find you a business-class flight to Tokyo with points, miles, or cash. It searches award availability across major mileage programs, compares against cash prices, uses your loyalty balances, and tells you the best play, with the math.

## Free-first

**Every core capability works with zero paid API keys.** Paid keys are optional upgrades, never prerequisites. With nothing configured you already get:

- Cash flight search (Skiplagged, Kiwi)
- Hotel search (Trivago) and short-term rentals (Airbnb)
- Ferry search (Ferryhopper)
- Award availability for roughly the next 60 days (seats.aero MCP, cached)

The only thing genuinely behind a paywall is **live** award search beyond 60 days plus alerts (seats.aero Pro, optional). Everything else has a keyless path.

## Quick start (zero keys)

### Claude Code

```
/plugin marketplace add isaacsvb/Travel-hacking-vilass
/plugin install travel-hacker@travel-hacker-marketplace
```

Then run `claude` and ask it to plan a trip. The keyless MCP servers are active immediately.

### Codex

```
codex plugin marketplace add isaacsvb/Travel-hacking-vilass
```

Then start Codex; the `travel-hacker` plugin appears in `/plugins`.

### OpenCode (clone path)

OpenCode has no plugin format, so clone the repo and launch from inside it:

```bash
git clone https://github.com/isaacsvb/Travel-hacking-vilass.git
cd Travel-hacking-vilass
opencode
```

`opencode.json` (MCP) and `AGENTS.md` (instructions) are auto-discovered.

### Contributors

Load the plugin from the working tree, no install:

```bash
claude --plugin-dir .
```

## Optional keys (upgrades only)

Run the setup script to add any of these safely (masked input, validated, backed up, never echoed):

```bash
bash scripts/setup-keys.sh          # macOS / Linux / WSL
# or
powershell -File scripts/setup-keys.ps1   # Windows
```

| Key | Unlocks | Cost |
|-----|---------|------|
| `SEATS_AERO_API_KEY` | live award search, dates beyond ~60 days, alerts | seats.aero Pro |
| `DUFFEL_API_KEY` | cleaner per-fare-class GDS cash pricing | free to search |
| `AWARDWALLET_API_KEY` + `AWARDWALLET_USER_ID` | auto-pull balances and elite status | AwardWallet Business |
| `LITEAPI_API_KEY` | live hotel rates | LiteAPI |

See [`.env.example`](.env.example) for details. If a key is missing, the toolkit silently uses the keyless path; it never gates on a key.

## What's included

### MCP servers

| Server | Does | Key |
|--------|------|-----|
| Skiplagged | cash flights, hidden-city | none |
| Kiwi | cash flights, virtual interlining | none |
| Trivago | hotel metasearch | none |
| Ferryhopper | ferries | none |
| Airbnb | short-term rentals | none |
| seats.aero | award availability (cached ~60d keyless; Pro for live/alerts) | none / Pro |
| LiteAPI | live hotel rates | optional |

### Skills

- **Orchestration:** `plan-trip` (hero), `compare-flights`, `compare-hotels`, `trip-calculator`, `getting-started`
- **Flights:** `seats-aero`, `duffel`, `browser-collector` (opt-in)
- **Loyalty:** `awardwallet`, `transfer-partners`
- **Reference (auto-load):** `flight-search-strategy`, `points-valuations`, `partner-awards`, `alliances`, `sweet-spots`, `fallback-and-resilience`

### Reference data

Versioned JSON in `data/` (alliances, partner-award mappings, sweet spots, transfer ratios, point valuations). Editable without code changes.

## How it works

Skills use **progressive disclosure**: the agent loads only each skill's name + description at session start, and the full body only when it decides to use it. MCP config is auto-discovered per agent (`.mcp.json` for Claude Code, `opencode.json` for OpenCode, bundled config for the Codex plugin). The `CLAUDE.md` / `AGENTS.md` system prompt encodes the free-first rules so the agent tries keyless sources first, adds keyed sources when present, and never gates on a missing key.

## Example prompts

```
Plan a trip to Lisbon in business class, dates flexible.
Find me the cheapest business-class award from the US West Coast to Tokyo.
Compare points vs cash for JFK to London next March.
Find hotels in Stockholm, include Airbnb.
What are my options to get to Tokyo on miles?
```

## Scraping (opt-in, off by default)

The `browser-collector` skill is a Playwright template for sites with no API. It is **off by default and never required** for any core capability. Scraping airline/portal sites typically violates their Terms of Service and is actively blocked; enable a collector only for a target you are authorized to automate.

## Optional module: monitoring backend

A standalone Python monitoring service (scheduler + award monitor + CPM calculator + n8n/Telegram alerts) is specified separately. It is optional and not required to use the toolkit.

## Verify the install

```bash
bash scripts/smoke-test.sh
```

Validates skill frontmatter, MCP config JSON, plugin manifests, data files, and the free-first keyless guarantee.

## License

MIT
