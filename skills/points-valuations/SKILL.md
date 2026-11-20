---
name: points-valuations
description: Cents-per-point (CPP) formula, floor and ceiling valuations per program, and the rules for deciding points vs cash. Auto-loads when comparing redemptions or judging whether a redemption is good value. Trigger phrases include cents per point, CPP, is this a good redemption, points vs cash, redemption value.
category: reference
summary: CPP formula and floor/ceiling valuation rules for points vs cash.
api_key: None (free)
---

# Points Valuations

## The CPP formula

```
CPP = (cash_price - award_cash_fees) / points * 100
```

- `cash_price` — the comparable cash fare in the same cabin.
- `award_cash_fees` — ALL out-of-pocket cost on the award: taxes, fuel/carrier surcharges, booking fees.
- `points` — miles/points spent (use effective points if transferring in; see `transfer-partners`).

Result is cents per point.

## Decision rule

Compare the CPP to the program's **floor** valuation in `data/points-valuations.json`:

- **CPP >= floor** -> good use of points.
- **CPP >= ceiling** -> exceptional; flag it.
- **CPP < floor** -> poor; recommend paying cash instead.

Default to the floor for decisions. Floors are conservative on purpose.

## Opportunity cost

Burning a transferable currency on a low-CPP redemption is wasteful when a high-CPP option exists. Example: using Chase UR at 1.2 CPP in a portal when Hyatt at 1.5+ CPP is available is a bad trade.

## When cash is unavailable

If there is no comparable cash fare, give an absolute valuation using the program's reference CPP and clearly mark the comparison as incomplete. Never fabricate a cash price.

## Data

All floor/ceiling values live in `data/points-valuations.json` (credit-card points, airline miles, hotel points). Cite that file; don't hard-code numbers in prose.
