---
name: compare-hotels
description: Unified hotel search across keyless metasearch and Airbnb, with chain-to-loyalty mapping and points-vs-cash for branded properties. Optional LiteAPI adds live rates. Trigger phrases include find hotels, hotel search, where to stay, Airbnb, hotel points vs cash.
category: hotels
summary: Hotel comparison across Trivago, Airbnb, and optional LiteAPI, with loyalty mapping.
api_key: Uses individual skill keys (works keyless)
---

# Compare Hotels

Free-first hotel search and comparison.

## Sources

- **Trivago** (keyless MCP) — hotel metasearch across booking sites.
- **Airbnb** (keyless MCP) — short-term rentals.
- **LiteAPI** (optional `LITEAPI_API_KEY`) — live bookable rates. Skip silently if no key.

## Workflow

1. Search Trivago + Airbnb (keyless); add LiteAPI if keyed.
2. When results include branded chain properties (Marriott, Hilton, Hyatt, IHG, Accor), map the brand to its loyalty program and compare points vs cash:
   - Hyatt is usually strong value (floor ~1.4 CPP).
   - Hilton floor (~0.4 CPP) is usually worse than cash.
   - Check `data/points-valuations.json` for the program floor/ceiling.
3. Present results as a markdown table (property, nightly cash, points option + CPP, notes), then a recommendation.

## Notes

- If LiteAPI errors or is unkeyed, keyless discovery still works (`fallback-and-resilience`).
- Airbnb scrapes a site; be reasonable with request volume.
