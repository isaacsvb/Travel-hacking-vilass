"""Pure value calculation: CPM and value classification. No I/O, fully testable."""

from __future__ import annotations

from .models import ValueClass


def compute_cpm(cash_price_usd: float, award_fees_usd: float, miles: int) -> float | None:
    """Cents per mile = (cash_price - award_fees) / miles * 100.

    Returns None if miles is non-positive. award_fees must include ALL
    out-of-pocket cost on the award (taxes, fuel/carrier surcharges).
    """
    if miles is None or miles <= 0:
        return None
    net_cents = (cash_price_usd - award_fees_usd) * 100.0
    return round(net_cents / miles, 3)


def classify_value(cpm: float | None, floor: float, ceiling: float) -> ValueClass:
    """Classify a redemption against a program's floor/ceiling valuation (in CPM).

    - cpm >= ceiling  -> EXCEPTIONAL
    - cpm >= floor    -> GOOD
    - cpm >= floor*0.7 -> MEDIOCRE
    - else            -> POOR
    None cpm (unknown) is treated as POOR so it never triggers an alert.
    """
    if cpm is None:
        return ValueClass.POOR
    if cpm >= ceiling:
        return ValueClass.EXCEPTIONAL
    if cpm >= floor:
        return ValueClass.GOOD
    if cpm >= floor * 0.7:
        return ValueClass.MEDIOCRE
    return ValueClass.POOR


def effective_miles(direct: int, transfer_amounts: list[int]) -> int:
    """Effective balance = direct + the single best transferable top-up.

    transfer_amounts are already ratio-adjusted (program-miles the user could
    bring in from each held card currency). We take the max, not the sum,
    because you generally transfer from one currency per redemption.
    """
    best_transfer = max(transfer_amounts, default=0)
    return direct + best_transfer


def is_high_value(value_class: ValueClass) -> bool:
    """High-value = GOOD or better. Used as the alert gate."""
    return value_class in (ValueClass.GOOD, ValueClass.EXCEPTIONAL)
