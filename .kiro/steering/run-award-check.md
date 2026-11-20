---
inclusion: manual
---

# Run an award check on demand

When the user asks you to "check awards", "run a check", or "see if there's award space" for a route, do this:

1. Figure out the route, date range, and cabin from their message (ask once if missing).
2. Run the local checker (it does not stay running — one shot):

```bash
cd monitor && PYTHONPATH=src python3 -m th_monitor.cli check \
  --from <ORIGIN> --to <DEST> --start <YYYY-MM-DD> --end <YYYY-MM-DD> \
  --cabin <economy|premium_economy|business|first> --json
```

Add `--balances balances.json` if the user has a `monitor/balances.json` so results gate by what they can actually reach. Add `--all` to show everything, not just high-value.

3. Read the JSON it prints (also saved to `monitor/output/latest.json`).
4. Present the opportunities as a markdown table with the CPM math, highlight sweet spots (`sweet_spot_id`), and note any `source_warnings` (a source being down is NOT "no availability") and `needs_verification` flags (stale data — verify before booking).
5. If `httpx` is missing, tell the user to run `pip install -e monitor` once; the keyless cached search needs it for the network call.

This is on-demand only. There is no background monitoring and no alerts — the user runs it (or asks you to) when they want an answer.
