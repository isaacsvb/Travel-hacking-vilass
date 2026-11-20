---
name: flight-search-strategy
description: The canonical multi-source flight search workflow, free-first. Load before any flight search. Covers source priority (keyless first, keyed as upgrade), parallel search order, award-vs-cash comparison, and common failure modes. Trigger phrases include flight search, find flights, best way to fly, award search, points vs cash.
category: reference
summary: Canonical free-first multi-source flight search workflow.
api_key: None (free)
---

# Flight Search Strategy

The workflow for answering any "find me a flight" or "points vs cash" question. Free-first: keyless sources are the base; keyed sources are upgrades.

## Source priority

**Cash fares**
1. Skiplagged (keyless MCP) — base, incl. hidden-city.
2. Kiwi (keyless MCP) — base, virtual interlining / creative routing.
3. Duffel (optional `DUFFEL_API_KEY`) — cleaner per-fare-class GDS pricing. Skip silently if no key.

**Award availability**
1. seats.aero MCP (keyless) — cached availability for ~the next 60 days. Always try this.
2. seats.aero live (optional `SEATS_AERO_API_KEY` or Pro sign-in) — live search, dates beyond 60 days, alerts.

## Workflow

1. Confirm route, dates (and flexibility), travelers, cabin. Ask once if missing.
2. Search cash and award sources **in parallel**. If a source errors or is rate-limited, skip it — an error is NOT "no availability."
3. For awards, pull ALL programs first; do not pre-filter by source. Then gate each option by reachability (see `partner-awards` + `transfer-partners`).
4. Compute CPP for each award option (see `points-valuations` + `trip-calculator`).
5. Flag matches against `data/sweet-spots.json`.
6. Present a ranked recommendation with the math.

## Failure modes to avoid

- Treating a 401/429/5xx as "sold out." It is not. Continue with other sources and say the source was unavailable.
- Pre-filtering award programs before pulling availability (you miss cross-alliance sweet spots like Virgin Atlantic to ANA).
- Quoting a redemption value without including taxes/fuel surcharges in the CPP math.
- Booking on stale cached data (24h+) without advising a verify-on-airline-site step.

## Multiple travelers

Always search for the requested seat count. Award space for 1 seat does not guarantee 2.
