---
name: partner-awards
description: Which loyalty program can issue award tickets on which operating airline, including cross-alliance and bilateral partnerships, plus the reachability workflow. Auto-loads when figuring out how to book a specific airline with points. Trigger phrases include which program books, how do I book this airline, can I redeem on, transfer path, reachability.
category: reference
summary: Which program books which airline, plus the reachability workflow.
api_key: None (free)
---

# Partner Awards

Determines whether a user can actually redeem on a given airline, and the cheapest program to do it.

## Reachability workflow

For each availability record:

1. Look up the operating carrier in `data/partner-awards.json` to find which programs can issue the ticket.
2. For each such program, check the user's reachability:
   - **Direct balance** sufficient, OR
   - A **transfer path** exists in `data/transfer-partners.json` from a currency the user holds, with enough effective (ratio-adjusted) points.
3. Drop programs the user cannot reach before computing CPP or ranking.

## Effective balance

```
effective_points(program) = direct_balance + max(ratio_adjusted transferable from each held currency)
```

Never dismiss a program because the direct balance is zero if it is reachable by transfer. Example: 0 United miles but 145K Chase UR (1:1) = 145K effective United miles.

## Cross-alliance highlights

- **Virgin Atlantic to ANA** — the single most valuable cross-alliance path; ANA first/business far cheaper than any Star Alliance program. ANA booked by phone.
- **Etihad to American** — Etihad's fixed chart for AA metal often beats AA's own dynamic pricing.

See `data/partner-awards.json` `cross_alliance_highlights` for the current list. Verify partner availability on the booking program's own site before transferring (transfers are one-way).
