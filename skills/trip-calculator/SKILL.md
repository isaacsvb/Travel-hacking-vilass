---
name: trip-calculator
description: Answers cash vs points with math. Computes cents-per-point including taxes and surcharges, applies transfer ratios and bonuses, and factors opportunity cost. Trigger phrases include should I use points or cash, is this worth it, cents per point, calculate value.
category: orchestration
summary: Cash vs points decision answered with CPP math, transfer ratios, and opportunity cost.
api_key: None (free, local data)
---

# Trip Calculator

Turns raw numbers into a points-vs-cash decision. Uses `points-valuations` and `transfer-partners`.

## Steps

1. Get the comparable cash price (same cabin/route/date) and the award: points + ALL cash fees (taxes, surcharges, booking fees).
2. Compute CPP:
   ```
   CPP = (cash_price - award_cash_fees) / points * 100
   ```
3. If the points come via transfer, use effective points after the ratio (and any active bonus). Verify the transfer path exists in `data/transfer-partners.json`.
4. Compare CPP to the program floor/ceiling in `data/points-valuations.json`:
   - at/above floor -> good; at/above ceiling -> exceptional; below floor -> pay cash.
5. Factor opportunity cost: don't burn a flexible currency at low CPP when a high-CPP option exists.
6. State the recommendation plainly, e.g. "Use 52.5K Virgin points for this ANA business seat: 2.1 CPP against the $1,900 cash fare, above the 1.0 floor. You can reach it via Chase UR 1:1."

## When cash is unavailable

Give an absolute valuation from the program reference CPP and mark the comparison incomplete. Never invent a cash price.
