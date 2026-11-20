---
name: awardwallet
description: Auto-pull loyalty balances and elite status from AwardWallet when configured. Optional. Absent the key, ask the user for balances once or reason from sweet spots. Trigger phrases include my balances, how many miles do I have, check my points, elite status.
category: loyalty
summary: Optional auto-pull of loyalty balances. Falls back to user-supplied balances.
api_key: AwardWallet Business (optional)
---

# AwardWallet (optional balances)

Optional convenience for pulling the user's balances automatically. Not required.

## When keyed

If both `AWARDWALLET_API_KEY` and `AWARDWALLET_USER_ID` are set, pull current balances and elite status without asking. Use them to compute effective balances (`transfer-partners`) and to confirm the user can cover a redemption.

## When not keyed

Ask the user once for the balances relevant to the trip, or give advice that doesn't depend on exact balances (sweet-spot reasoning). Mention once at the end that setting AwardWallet would let you pull balances automatically next time — but only if balances would have changed the recommendation.

## Notes

- Never ask "do you have AwardWallet set up?" as a gate. Try it if the env vars are present; otherwise ask for balances directly.
- Flag points expiring soon or status up for renewal if the data shows it.
