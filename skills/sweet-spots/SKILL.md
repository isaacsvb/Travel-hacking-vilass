---
name: sweet-spots
description: Catalog of high-value award redemptions (fixed rate plus the partner booking path). Auto-loads when evaluating whether an itinerary matches a known legendary redemption. Trigger phrases include sweet spot, best redemption, legendary award, high value redemption.
category: reference
summary: Catalog of high-value redemptions with booking paths.
api_key: None (free, local data)
---

# Sweet Spots

Known high-value redemptions. Data in `data/sweet-spots.json`. Each entry pairs a route/region pattern with the cheapest program and the booking path.

## How to use

1. When an itinerary is found, check whether it matches a sweet spot's `route_pattern` + `cabin`.
2. If it matches, annotate the option with the sweet-spot id and expected miles, and flag any gap between observed and expected miles cost.
3. Follow the `booking_path` and note surcharges.

## Highlights (verify current rates in the data file)

- **ANA business/first via Virgin Atlantic** from the US West Coast — far below any Star Alliance program. Phone booking.
- **US East Coast to Madrid business on Iberia Avios** — ~40,500 Avios off-peak.
- **Qatar Qsuites via Qatar Privilege Club** — top business product, low surcharges.
- **United domestic via Turkish Miles&Smiles** — 10K short-haul.
- **Lufthansa First via Aeroplan** — one of the few partner paths to LH First.

Rates devalue. Always cite `data/sweet-spots.json` (it carries `last_updated`) and verify on the airline/program site before booking or transferring.
