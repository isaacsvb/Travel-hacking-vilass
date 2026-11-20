---
name: duffel
description: Optional cash flight prices via Duffel for cleaner per-fare-class GDS data. Search is free (you pay only if you book elsewhere). Absent the key, keyless cash sources (Skiplagged, Kiwi) cover cash search. Trigger phrases include cash fare, per-fare-class pricing, GDS price, business class cash price.
category: flights
summary: Optional per-fare-class GDS cash pricing. Keyless cash search works without it.
api_key: Duffel (free to search)
---

# Duffel (optional cash fares)

An optional upgrade for cleaner cash pricing. The toolkit does cash search fine without it via Skiplagged + Kiwi.

## When keyed

If `DUFFEL_API_KEY` is set, use Duffel to fetch per-fare-class cash prices for the requested route/date/cabin. This gives cleaner GDS pricing than the keyless metasearch sources and is useful for a precise points-vs-cash comparison.

## When not keyed

Skip Duffel silently and use Skiplagged + Kiwi (keyless). Do not ask the user whether they have a Duffel key — just try the keyless sources.

## Notes

- Search is free; booking is out of scope for this toolkit.
- Feed the Duffel cash price into the CPP math (`points-valuations`).
- If Duffel errors, fall back to keyless cash sources (`fallback-and-resilience`).
