"""On-demand pipeline: search -> reachability -> CPM -> ranked opportunities.

Pure orchestration over injectable pieces so it is testable without network.
"""

from __future__ import annotations

from dataclasses import dataclass

from .calculator import classify_value, compute_cpm, effective_miles, is_high_value
from .knowledge import Knowledge
from .models import Availability, Cabin, Opportunity, ValueClass


@dataclass
class CheckResult:
    opportunities: list[Opportunity]
    source_warnings: list[str]
    data_warnings: list[str]
    scanned: int


def evaluate(
    availabilities: list[Availability],
    kb: Knowledge,
    held_currencies: dict[str, int] | None = None,
    direct_balances: dict[str, int] | None = None,
    min_seats: int = 1,
    only_high_value: bool = True,
    cash_prices: dict[str, float] | None = None,
) -> list[Opportunity]:
    """Turn raw availability into ranked opportunities.

    held_currencies: {card_currency_id: balance} for transfer reachability.
    direct_balances: {program_id: miles} already held directly.
    cash_prices: optional {route|date|cabin: cash_usd} to feed CPM. When absent
                 for a record, CPM is computed as None and marked incomplete.
    """
    held_currencies = held_currencies or {}
    direct_balances = direct_balances or {}
    cash_prices = cash_prices or {}
    out: list[Opportunity] = []

    for a in availabilities:
        if min_seats and (a.seats or 0) < min_seats:
            continue

        # Reachability: does the user hold enough, directly or via transfer?
        direct = direct_balances.get(a.program, 0)
        transfers = kb.transfer_options(a.program, held_currencies)
        reachable_miles = effective_miles(direct, transfers)
        reachable = a.miles_cost is not None and reachable_miles >= a.miles_cost
        # If the user gave no balances at all, don't gate on reachability.
        if not held_currencies and not direct_balances:
            reachable = True

        # Value.
        val = kb.program_valuation(a.program)
        cash_key = f"{a.origin}-{a.destination}|{a.date}|{a.cabin.value}"
        cash = cash_prices.get(cash_key)
        cash_available = cash is not None
        cpm = None
        if cash_available and a.miles_cost:
            cpm = compute_cpm(cash, a.cash_fees_usd or 0.0, a.miles_cost)
        if val:
            floor, ceiling = val
            vclass = classify_value(cpm, floor, ceiling) if cpm is not None else ValueClass.MEDIOCRE
        else:
            vclass = ValueClass.MEDIOCRE

        notes: list[str] = []
        if not cash_available:
            notes.append("cash price unavailable; value is an estimate")
        if a.is_stale():
            notes.append("cached data is 24h+ old; verify on the airline site before booking")

        # Sweet-spot match.
        ss_id, booking = _match_sweet_spot(a, kb)

        opp = Opportunity(
            availability=a,
            cpm=cpm,
            cash_price_usd=cash,
            value_class=vclass,
            reachable=reachable,
            sweet_spot_id=ss_id,
            booking_path=booking,
            needs_verification=a.is_stale(),
            dedup_key=f"{cash_key}|{a.program}|{a.operating_carrier}",
            cash_price_available=cash_available,
            notes=notes,
        )

        gate = (not only_high_value) or is_high_value(vclass) or ss_id is not None
        if reachable and gate:
            out.append(opp)

    # Rank: sweet spots first, then by CPM desc (None last).
    out.sort(key=lambda o: (o.sweet_spot_id is None, -(o.cpm or -1)))
    return out


def _match_sweet_spot(a: Availability, kb: Knowledge) -> tuple[str | None, str | None]:
    for ss in kb.sweet_spots.get("sweet_spots", []):
        if ss.get("program") != a.program:
            continue
        if ss.get("cabin") != a.cabin.value:
            continue
        return ss.get("id"), ss.get("booking_path")
    return None, None
