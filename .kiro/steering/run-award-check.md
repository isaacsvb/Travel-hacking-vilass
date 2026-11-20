---
inclusion: manual
---

# Run an award check on demand

When the user asks you to "check awards", "run a check", or "see if there's award space" for a route, do this.

## Step 0 — understand the two seats.aero surfaces (important)

seats.aero has NO keyless REST endpoint. The free path is the **seats.aero MCP server** (configured in `.kiro/settings/mcp.json`), which covers departures from today through ~60 days with an IP-based daily limit. The Partner API requires a paid key. So:

- **Free path (default):** YOU (Kiro) call the seats.aero MCP tool directly for the search, then feed its JSON into the local calculator for CPM/reachability/ranking.
- **Keyed path:** if `SEATS_AERO_API_KEY` is set, the CLI can query the Partner API directly (live + beyond 60 days).

## Steps

1. Get route, date range, cabin, and seat count from the user (ask once if missing). Remember the free window is ~60 days out.
2. **Call the seats.aero MCP tool** for the route/dates/cabin (this is the keyless search). Save its JSON output to a file, e.g. `monitor/output/mcp-raw.json`.
3. Run the local calculator on that JSON to rank by value and gate by reachability:

```bash
cd monitor && PYTHONPATH=src python3 -m th_monitor.cli check \
  --from <ORIGIN> --to <DEST> --start <YYYY-MM-DD> --end <YYYY-MM-DD> \
  --cabin <economy|premium_economy|business|first> --seats <N> \
  --mcp-json output/mcp-raw.json --json
```

Add `--balances balances.json` if the user has one, so results gate by what they can actually reach. Add `--all` to show everything, not just high-value.

4. If `SEATS_AERO_API_KEY` is set and you prefer the direct path, omit `--mcp-json` and the CLI queries the Partner API itself.
5. Present the opportunities as a markdown table with the CPM math, highlight sweet spots (`sweet_spot_id`), and surface `source_warnings` (a source being unavailable is NOT "no availability") and `needs_verification` (stale data — verify before booking).

## Honesty rules

- A source error or an auth rejection is NEVER "no award space". Say the source was unavailable and why.
- Do not claim a keyless REST search happened — the keyless path is the MCP tool you (Kiro) call.
- If the user's dates run past ~60 days and no key is set, say that part of the range needs a Pro key; don't silently return empty.

This is on-demand only. No background monitoring, no alerts.
