---
name: plan-trip
description: Guided end-to-end trip planner and the hero command of the toolkit. Plans flights, hotels, and points in one flow, free-first. Trigger phrases include plan a trip, plan my trip to, help me get to, book a trip.
category: orchestration
summary: Guided end-to-end trip planner. Flights plus hotels plus points, free-first.
api_key: None (orchestrates other skills)
---

# Plan Trip

The hero workflow. Plans a whole trip and gives an opinionated, math-backed recommendation. Free-first throughout.

## Flow

1. **Gather context once:** origin, destination, dates (+ flexibility), travelers, cabin, and any hotel preference. Ask in a single message if missing.
2. **Balances:** pull via AwardWallet if configured; otherwise ask once for relevant balances or reason from sweet spots.
3. **Flights:** run `compare-flights` (keyless cash + award; keyed upgrades if present). Gate awards by reachability; compute CPP; flag sweet spots.
4. **Hotels:** run `compare-hotels` (Trivago + Airbnb keyless; LiteAPI if keyed). Map branded chains to loyalty programs and compare points vs cash.
5. **Ground/extras (optional):** ferries via Ferryhopper for island/coastal legs.
6. **Recommend:** present flights and hotels as markdown tables, each followed by a ranked recommendation with the math. Call out the single best play.
7. **Freshness + verify:** note award-data freshness; advise verifying stale data before booking or transferring.
8. **One upgrade hint (optional):** if a missing optional key would have materially improved this plan, mention that one key in a single closing line.

## Principles

- Never gate on a missing key. Try keyless first; add keyed sources when present.
- Show CPP math for every points option.
- Be opinionated: rank, don't dump.
