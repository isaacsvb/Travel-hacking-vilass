---
name: seats-aero
description: Award flight availability across major mileage programs via the seats.aero MCP. Keyless cached search works for the next ~60 days with no sign-in; an optional Pro key or sign-in adds live search, dates beyond 60 days, and alerts. Trigger phrases include award availability, find business class with miles, award search, premium seat availability.
category: flights
summary: Award availability search. Keyless cached ~60 days; optional Pro for live and alerts.
api_key: None for 60 days, seats.aero Pro for the rest
---

# seats.aero (award availability)

The primary award-availability source. **Free-first:** cached search works with no key.

## Keyless (always available)

Use the seats.aero MCP tools for cached availability across major mileage programs for roughly the next 60 days. No sign-in required. This is the default path and covers most near-term trips.

- Pull ALL programs first; do not pre-filter by source.
- Each result carries a freshness timestamp. Data is cached, not live.

## Optional upgrade (seats.aero Pro)

If `SEATS_AERO_API_KEY` is set or the MCP is signed in to Pro, you additionally get:
- Live search (not just cache),
- Dates beyond the ~60-day cached window,
- Award alerts.

If the key/sign-in is absent, skip these silently and use the cached path. Do not ask the user whether they have Pro before trying the keyless tools.

## Usage notes

- Note the freshness timestamp on every result. If 24h+ old, advise verifying on the airline site before booking or transferring points.
- Search for the requested seat count; 1 seat available does not guarantee 2.
- After pulling availability, gate each program by reachability (`partner-awards`) and compute CPP (`points-valuations`).
- An API error or rate limit is NOT "no availability" — see `fallback-and-resilience`.
