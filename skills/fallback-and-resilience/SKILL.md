---
name: fallback-and-resilience
description: What to do when a tool fails or a key is missing, free-first. Auto-loads on any search so errors degrade gracefully instead of being reported as no availability. Trigger phrases include tool failed, missing key, no results, 401, 429, rate limited, fallback.
category: reference
summary: Per-tool graceful degradation so errors never read as no availability.
api_key: None (free)
---

# Fallback and Resilience

The rules that keep the toolkit useful when a source is down or a key is missing.

## Core principle: error is not empty

A 401 / 403 / 429 / 5xx or a timeout is NOT "no availability" and NOT "sold out." When a source fails:

1. Skip that source and continue with the others.
2. Tell the user the source was unavailable (one short line), separately from the actual results.
3. Never present a failed source as if it returned zero results.

## Missing optional key

- The key is absent -> skip that Tier-1 source silently and use the keyless path. Do not ask the user whether they have the key before trying.
- If, and only if, the missing key would have materially improved THIS result, add one closing line suggesting it.

## Per-source fallback

| Source | If it fails / key missing | Fallback |
|---|---|---|
| Duffel (cash) | key missing or error | Skiplagged + Kiwi (keyless) |
| seats.aero live | no `SEATS_AERO_API_KEY` / Pro | seats.aero MCP cached (~60 days, keyless) |
| seats.aero cached | error | cash-only comparison; say award data was unavailable |
| AwardWallet | not configured | ask the user for balances once, or reason from sweet spots |
| LiteAPI (hotels) | key missing | Trivago + Airbnb (keyless) |

## Stale data

seats.aero is cached. Surface the freshness timestamp. If data is 24h+ old, mark the option as needing verification and advise checking the airline site before booking or transferring points.
