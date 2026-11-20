---
name: alliances
description: Airline alliance membership (Star Alliance, oneworld, SkyTeam) and which loyalty program each airline uses. Auto-loads when alliance structure or partner reasoning matters. Trigger phrases include which alliance, Star Alliance, oneworld, SkyTeam, alliance partner.
category: reference
summary: Alliance membership and loyalty-program mapping.
api_key: None (free)
---

# Alliances

Reference for which alliance an airline belongs to and which loyalty program it uses. Full data in `data/alliances.json`.

- **Star Alliance** — United, Air Canada (Aeroplan), Lufthansa (Miles & More), ANA, Singapore (KrisFlyer), Turkish (Miles&Smiles), TAP (Miles&Go), Avianca (LifeMiles).
- **oneworld** — American (AAdvantage), British Airways / Iberia / Qatar / Finnair (Avios), Cathay (Asia Miles), JAL, Qantas, Alaska (Atmos).
- **SkyTeam** — Delta (SkyMiles), Air France / KLM (Flying Blue), Korean Air (SKYPASS), Virgin Atlantic (Flying Club).
- **Non-alliance** — Emirates (Skywards), Etihad (Guest), JetBlue (TrueBlue), Southwest (Rapid Rewards, no partners).

Within an alliance, any member program can usually book any other member's seats. The high-value plays are often **cross-alliance** (see `partner-awards`), e.g. booking Star Alliance carrier ANA through SkyTeam member Virgin Atlantic.

Cite `data/alliances.json` for membership; it carries a `last_updated` date and changes as airlines switch alliances.
