---
name: transfer-partners
description: Find the cheapest transfer path from a credit-card currency to the airline or hotel program that offers the best redemption, using local data. Auto-loads when a transfer is involved. Trigger phrases include transfer points, which points should I use, cheapest transfer path, effective balance.
category: loyalty
summary: Cheapest transfer path from card points to loyalty programs, from local data.
api_key: None (free, local data)
---

# Transfer Partners

Maps transferable bank currencies (Amex MR, Chase UR, Bilt, Capital One, Citi TY) to airline/hotel programs with ratios. Data in `data/transfer-partners.json`.

## Effective balance

```
effective_points(program) = direct_balance + max(ratio-adjusted transferable from each held currency)
```

Never dismiss a program with a zero direct balance if it is reachable by transfer.

## Rules

1. Before recommending any transfer, verify the path exists in `data/transfer-partners.json`. If it is not there, do not assume it exists — the file may be stale or the path may not exist.
2. Most transfers are 1:1 but not all (e.g. Amex to Hilton is 1:2; some hotel transfers are 2:1). Apply the real ratio.
3. Transfers are usually one-way and irreversible. Confirm award space (ideally place a hold) before transferring.
4. Factor in any active transfer bonus (changes the effective ratio).

Cite `data/transfer-partners.json` for ratios rather than hard-coding them.
