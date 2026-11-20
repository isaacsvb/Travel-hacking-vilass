# Using this toolkit with Kiro

A step-by-step guide so you don't have to remember how the pieces fit together between sessions.

## The one thing to understand first

Kiro reads everything from the **workspace it's running in**. The toolkit's Kiro files (`.kiro/settings/mcp.json`, `.kiro/steering/`, and the `monitor/` tool) live in **this repository**. So a Kiro session only sees them if this repo is cloned into that session's workspace.

If a fresh Kiro session says "I don't see `#run-award-check`" or "the workspace is empty", it just means the repo isn't cloned there yet. Nothing is lost — it's all on GitHub in `main`.

## First-time setup in a new Kiro session

1. **Clone the repo into the session:**
   ```bash
   git clone https://github.com/isaacsvb/Travel-hacking-vilass.git
   ```
2. **Restart (or reopen) the session.** MCP servers are loaded when the sandbox starts, so the keyless seats.aero / Skiplagged / Kiwi / Trivago / Ferryhopper / Airbnb servers come online on the next start after the clone. (The steering files work immediately; only the MCP servers need the restart.)
3. You're ready. Ask Kiro to plan a trip, or run `#run-award-check`.

## How award search actually works (free-first, the honest version)

seats.aero has **no keyless REST endpoint** — its Partner API always needs a paid key. The genuinely free path is the **seats.aero MCP server** (departures today through ~60 days, IP-rate-limited), which **Kiro calls as an MCP tool**. So:

- **Free path (default, no key):**
  1. Kiro calls the seats.aero **MCP tool** for your route/dates/cabin.
  2. Kiro saves that JSON (e.g. to `monitor/output/mcp-raw.json`).
  3. Kiro runs the local ranker on it:
     ```bash
     cd monitor && PYTHONPATH=src python3 -m th_monitor.cli check \
       --from SSA --to YQR --start 2026-12-22 --end 2027-01-25 \
       --cabin economy --seats 2 --mcp-json output/mcp-raw.json --json
     ```
  4. Kiro presents the ranked opportunities with the CPM math.

- **Keyed path (optional, paid):** set `SEATS_AERO_API_KEY` and drop `--mcp-json`; the CLI queries the Partner API directly (live search + dates beyond ~60 days).

**What you never give up for free:** cash fares (Skiplagged, Kiwi), hotels (Trivago), ferries (Ferryhopper), stays (Airbnb) — all keyless MCP, always on.

## Running an on-demand check

In a Kiro session, type `#run-award-check` and tell Kiro the route, dates, cabin, and number of travelers. It runs the flow above. Nothing runs in the background and there are no alerts — it only acts when you ask.

Add your balances (optional) so results are gated by what you can actually reach: copy `monitor/balances.example.json` to `monitor/balances.json`, fill it in, and Kiro passes `--balances balances.json`. That file is gitignored — it never leaves your machine.

## Reading the result honestly

- **A source error or auth rejection is NOT "no award space."** Kiro will say the source was unavailable and why. Zero results from a failed call means "couldn't check", not "nothing available".
- **Stale data (24h+)** is flagged `needs_verification` — confirm on the airline site before booking or transferring points.
- **No cash price** means the CPM is an estimate; Kiro marks it incomplete.

## Long / complex routes (e.g. SSA -> YQR)

Some routes have no single-program award for the whole journey, especially for 2+ seats (example: Salvador, Brazil to Regina, Canada). For these:

1. **Split into legs via a hub** (e.g. SSA -> GRU, GRU -> a US/Canada gateway, gateway -> YQR). Ask Kiro to check each leg separately through the MCP, then combine.
2. **Mind the ~60-day free window.** Today-plus-60-days is the keyless limit. If your dates run past that (e.g. late January when it's late November), that part of the range needs **seats.aero Pro** (~$13/month) — there's no free way around it. Kiro will tell you which dates fall outside the free window instead of silently returning empty.
3. **Cheapest realistic path:** check near-term legs inside the 60-day window keyless, and only reach for a Pro key if you specifically need the far-out dates or live search.

## Quick reference

| You want | Do this |
|---|---|
| First use in a new session | clone the repo, restart the session |
| Plan a whole trip | ask Kiro: "plan a trip to X, dates, cabin" |
| On-demand award check | `#run-award-check` + route/dates/cabin/seats |
| Gate by your miles | create `monitor/balances.json` from the example |
| Dates beyond ~60 days / live search | set `SEATS_AERO_API_KEY` (seats.aero Pro) |
| Add any optional key safely | `bash scripts/setup-keys.sh` |

## Autonomous monitoring + alerts?

Out of scope on purpose — you asked for on-demand only. A spec for a background service with Telegram/n8n alerts exists at `docs/specs/backend-milhas/` if you ever change your mind.
