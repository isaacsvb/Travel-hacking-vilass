"""Award-availability source: seats.aero, free-first.

Keyless cached search works for ~60 days. If SEATS_AERO_API_KEY is set, the
Partner API is used for live search and dates beyond the cache window. A
network/auth error is never reported as "no availability" — it raises
SourceError so the caller can say the source was unavailable.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from .models import Availability, Cabin

PARTNER_BASE = "https://seats.aero/partnerapi"
CACHED_SEARCH = f"{PARTNER_BASE}/search"

# Map seats.aero cabin fields to our Cabin enum.
_CABIN_MAP = {
    "economy": Cabin.ECONOMY,
    "premium": Cabin.PREMIUM,
    "business": Cabin.BUSINESS,
    "first": Cabin.FIRST,
}


class SourceError(RuntimeError):
    """Raised when the source is unavailable. NOT the same as 'no availability'."""


class SeatsAeroSource:
    def __init__(self, api_key: str | None = None, timeout: float = 20.0):
        # Free-first: key is optional. When present, we can do live search.
        self.api_key = api_key or os.environ.get("SEATS_AERO_API_KEY")
        self.timeout = timeout

    @property
    def has_live(self) -> bool:
        return bool(self.api_key)

    def search(
        self,
        origin: str,
        destination: str,
        start_date: str,
        end_date: str,
        cabin: Cabin,
    ) -> list[Availability]:
        """Return normalized availability. Raises SourceError on failure."""
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["Partner-Authorization"] = self.api_key
        params = {
            "origin_airport": origin,
            "destination_airport": destination,
            "start_date": start_date,
            "end_date": end_date,
            "take": 500,
        }
        try:
            import httpx  # lazy import so the CLI still runs without the dep installed
        except ImportError as e:
            raise SourceError(
                "httpx is not installed; run `pip install -e monitor` to enable live "
                "search."
            ) from e
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(CACHED_SEARCH, params=params, headers=headers)
        except httpx.HTTPError as e:
            raise SourceError(f"seats.aero request failed: {e}") from e

        if resp.status_code in (401, 403):
            raise SourceError(
                "seats.aero rejected the request (auth). Cached keyless search "
                "may still work for the next ~60 days; a Pro key unlocks the rest."
            )
        if resp.status_code == 429:
            raise SourceError("seats.aero rate limit hit; try again shortly.")
        if resp.status_code >= 500:
            raise SourceError(f"seats.aero server error {resp.status_code}.")
        if resp.status_code != 200:
            raise SourceError(f"seats.aero returned {resp.status_code}.")

        try:
            payload = resp.json()
        except ValueError as e:
            raise SourceError(f"seats.aero returned non-JSON: {e}") from e

        return self._normalize(payload, cabin)

    def _normalize(self, payload: dict, want: Cabin) -> list[Availability]:
        out: list[Availability] = []
        for row in payload.get("data", []):
            route = row.get("Route", {})
            origin = route.get("OriginAirport") or row.get("OriginAirport", "")
            dest = route.get("DestinationAirport") or row.get("DestinationAirport", "")
            program = (row.get("Source") or "").lower()
            date = row.get("Date", "")
            last_seen = _parse_dt(row.get("ComputedLastSeen") or row.get("UpdatedAt"))

            for key, cabin in (
                ("JAvailable", Cabin.BUSINESS),
                ("FAvailable", Cabin.FIRST),
                ("WAvailable", Cabin.PREMIUM),
                ("YAvailable", Cabin.ECONOMY),
            ):
                if cabin is not want:
                    continue
                if not row.get(key):
                    continue
                prefix = key[0]
                miles = _to_int(row.get(f"{prefix}MileageCost"))
                fees = _milli_to_usd(row.get(f"{prefix}TotalTaxes"))
                seats = _to_int(row.get(f"{prefix}RemainingSeats"))
                carrier = row.get(f"{prefix}Airlines") or row.get("Carriers") or ""
                out.append(
                    Availability(
                        origin=origin,
                        destination=dest,
                        date=date,
                        program=program,
                        operating_carrier=str(carrier).split(",")[0].strip() or "unknown",
                        cabin=cabin,
                        miles_cost=miles,
                        cash_fees_usd=fees,
                        seats=seats,
                        source="seats_aero",
                        last_seen=last_seen,
                    )
                )
        return out


def _to_int(v) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _milli_to_usd(v) -> float | None:
    """seats.aero reports taxes in hundredths/thousandths depending on field; be defensive."""
    i = _to_int(v)
    if i is None:
        return None
    # TotalTaxes is in cents in the Partner API; convert to dollars.
    return round(i / 100.0, 2)


def _parse_dt(v) -> datetime:
    if not v:
        return datetime.now(timezone.utc)
    try:
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)
