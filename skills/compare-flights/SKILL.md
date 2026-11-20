---
name: compare-flights
description: Unified flight comparison across all award and cash sources in parallel, free-first, with CPP and reachability applied. The go-to skill when the user knows their dates. Trigger phrases include compare flights, best option, all options, find me a flight, award vs cash.
category: orchestration
summary: Unified award + cash flight comparison across all sources, free-first.
api_key: Uses individual skill keys (works keyless)
---

# Compare Flights

Runs the full flight comparison. Loads `flight-search-strategy` and `fallback-and-resilience` first.

## Workflow

1. Confirm route, dates, travelers, cabin (ask once if missing).
2. Search in parallel:
   - Cash: Skiplagged + Kiwi (keyless), Duffel (if keyed).
   - Award: seats.aero MCP cached (keyless), live if `SEATS_AERO_API_KEY`/Pro.
   Skip any source that errors; never report an error as "no availability."
3. Pull all award programs, then gate by reachability (`partner-awards` + `transfer-partners`).
4. Compute CPP per award option (`trip-calculator` + `points-valuations`); flag sweet-spot matches (`data/sweet-spots.json`).
5. Present one markdown table: each row = an option (cash or award) with price or miles+fees, CPP, stops, airline/program, freshness.
6. After the table: cheapest / fastest / best value, tradeoffs, and a clear recommendation.
7. Add at most one closing line about a missing optional key only if it would have improved this result.

## Example output shape

| Option | Price / Miles | CPP | Stops | Carrier / Program | Notes |
|---|---|---|---|---|---|
| Award | 52.5K + $100 | 2.1 | nonstop | ANA via Virgin Atlantic | sweet spot; cached 6h ago |
| Cash | $1,900 | — | nonstop | ANA | — |
