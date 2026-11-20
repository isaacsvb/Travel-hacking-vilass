---
name: getting-started
description: First-run onboarding. Detects which optional keys are configured, confirms the keyless capabilities that already work, points at the setup-keys script for upgrades, and shows sample prompts. Trigger phrases include getting started, setup, what can you do, how do I start, which keys do I need.
category: orchestration
summary: First-run onboarding and setup detector, free-first.
api_key: None
---

# Getting Started

Onboards a new user. The toolkit is free-first: a lot already works with zero keys.

## What works right now with NO keys

- Cash flight search (Skiplagged, Kiwi)
- Hotel search (Trivago), short-term rentals (Airbnb)
- Ferry search (Ferryhopper)
- Award availability for roughly the next 60 days (seats.aero MCP, cached)

Try: "Find me a business-class flight to Tokyo with points or cash next month."

## Optional upgrades (only if you want them)

Detect which are set by checking the environment, and tell the user what's active vs available:

| Env var | Unlocks | Cost |
|---|---|---|
| `SEATS_AERO_API_KEY` | live award search, dates beyond ~60 days, alerts | seats.aero Pro |
| `DUFFEL_API_KEY` | cleaner per-fare-class cash pricing | free to search |
| `AWARDWALLET_API_KEY` + `AWARDWALLET_USER_ID` | auto-pull balances and status | AwardWallet Business |
| `LITEAPI_API_KEY` | live hotel rates | LiteAPI |

To add keys safely, run the setup script: `scripts/setup-keys.sh` (macOS/Linux) or `scripts/setup-keys.ps1` (Windows). It prompts with masked input, validates, writes to your shell rc with a backup, and never echoes the value.

## Sample prompts

- "Plan a trip to Lisbon in business class, dates flexible."
- "Compare points vs cash for JFK to London next March."
- "Find hotels in Stockholm, include Airbnb."
- "What's the cheapest way to get to Tokyo on miles?"
