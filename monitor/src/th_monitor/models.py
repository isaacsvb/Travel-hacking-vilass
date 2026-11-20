"""Canonical data models shared across the monitor pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Cabin(str, Enum):
    ECONOMY = "economy"
    PREMIUM = "premium_economy"
    BUSINESS = "business"
    FIRST = "first"


class ValueClass(str, Enum):
    POOR = "poor"
    MEDIOCRE = "mediocre"
    GOOD = "good"
    EXCEPTIONAL = "exceptional"


@dataclass(frozen=True)
class Availability:
    """One normalized award-availability record from any source."""

    origin: str
    destination: str
    date: str  # ISO date (YYYY-MM-DD)
    program: str
    operating_carrier: str
    cabin: Cabin
    miles_cost: int | None
    cash_fees_usd: float | None
    seats: int | None
    source: str
    last_seen: datetime

    def is_stale(self, threshold_hours: int = 24) -> bool:
        age = datetime.now(timezone.utc) - self.last_seen
        return age.total_seconds() > threshold_hours * 3600


@dataclass(frozen=True)
class Opportunity:
    """A reachable, valued award opportunity ready to alert on."""

    availability: Availability
    cpm: float | None
    cash_price_usd: float | None
    value_class: ValueClass
    reachable: bool
    sweet_spot_id: str | None
    booking_path: str | None
    needs_verification: bool
    dedup_key: str
    cash_price_available: bool = True
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        a = self.availability
        return {
            "route": f"{a.origin}-{a.destination}",
            "date": a.date,
            "cabin": a.cabin.value,
            "program": a.program,
            "operating_carrier": a.operating_carrier,
            "miles_cost": a.miles_cost,
            "cash_fees_usd": a.cash_fees_usd,
            "cash_price_usd": self.cash_price_usd,
            "cash_price_available": self.cash_price_available,
            "seats": a.seats,
            "cpm": self.cpm,
            "value_class": self.value_class.value,
            "reachable": self.reachable,
            "sweet_spot_id": self.sweet_spot_id,
            "booking_path": self.booking_path,
            "needs_verification": self.needs_verification,
            "source": a.source,
            "last_seen": a.last_seen.isoformat(),
            "dedup_key": self.dedup_key,
            "notes": self.notes,
        }
