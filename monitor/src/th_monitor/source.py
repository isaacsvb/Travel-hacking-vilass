"""Award-availability source: seats.aero, free-first (corrected).

Important design note (why this file looks the way it does):

seats.aero has TWO surfaces:
  1. The Partner API (https://seats.aero/partnerapi/search) — ALWAYS requires a
     Partner key. There is NO keyless REST endpoint; an unauthenticated call
     returns 401 missing_partner_key. (Verified against the live endpoint.)
  2. The public MCP server (https://seats.aero/mcp) — this is the genuinely
     KEYLESS path, covering departures from today through ~60 days, with an
     IP-based daily limit. It is consumed by an MCP client (Kiro, Claude, etc.),
     NOT by a standalone Python HTTP call.

So the free-first keyless path for THIS tool is: the agent (Kiro) calls the
seats.aero MCP tool and feeds the resulting availability JSON into the pipeline.
This module therefore:
  - with SEATS_AERO_API_KEY set  -> queries the Partner API directly;
  - without a key                -> does NOT pretend to do a keyless REST call
    (that always 401s). It raises SourceError pointing at the MCP path, and the
    pipeline can instead consume availability from a JSON file/stdin that the
    MCP produced (`from_mcp_json`).

A source failure is never reported as "no availability".
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from .models import Availability, Cabin

PARTNER_BASE = "https://seats.aero/partnerapi"
PARTNER_SEARCH = f"{PARTNER_BASE}/search"
MCP_URL = "https://seats.aero/mcp"


class SourceError(RuntimeError):
    """Raised when the source is unavailable. NOT the same as 'no availability'."""


class KeylessPathUnavailable(SourceError):
    """No Partner key is set, so this tool cannot do a direct HTTP search.

    The keyless path is the seats.aero MCP server, which the agent (Kiro) calls.
    Feed its JSON output into the pipeline via `from_mcp_json`.
    """


class SeatsAeroSource:
    def __init__(self, api_key: str | None = None, timeout: float = 20.0):
        # Free-first: the key is optional, but a DIRECT HTTP search needs it.
        # The keyless path is the MCP server (handled by the agent), not here.
        self.api_key = api_key or os.environ.get("SEATS_AERO_API_KEY")
        self.timeout = timeout

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)

    def search(
        self,
        origin: str,
        destination: str,
        start_date: str,
        end_date: str,
        cabin: Cabin,
    ) -> list[Availability]:
        """Partner-API search. Requires a key. Raises SourceError on failure.

        Without a key this raises KeylessPathUnavailable (the keyless path is the
        MCP server, used by the agent) rather than making a call that always 401s.
        """
        if not self.api_key:
            raise KeylessPathUnavailable(
                "No SEATS_AERO_API_KEY set. seats.aero has no keyless REST endpoint "
                "(the Partner API always requires a key). The free path is the "
                "seats.aero MCP server (https://seats.aero/mcp), which Kiro calls "
                "directly for the next ~60 days. Ask Kiro to run the seats.aero MCP "
                "search and feed the result in with `--mcp-json <file>`, or set a "
                "Pro key to enable direct search here."
            )

        headers = {"accept": "application/json", "Partner-Authorization": self.api_key}
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
                "httpx is not installed; run `pip install -e monitor` to enable "
                "direct Partner-API search."
            ) from e
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(PARTNER_SEARCH, params=params, headers=headers)
        except httpx.HTTPError as e:
            raise SourceError(f"seats.aero request failed: {e}") from e

        if resp.status_code in (401, 403):
            raise SourceError(
                "seats.aero rejected the Partner key (401/403). Check the key, or "
                "use the keyless MCP path via Kiro."
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

        return normalize_payload(payload, cabin)


def from_mcp_json(payload: dict, cabin: Cabin) -> list[Availability]:
    """Normalize availability JSON that came from the keyless seats.aero MCP.

    Accepts either the Partner-API shape ({"data": [...]}) or a bare list, so a
    agent can paste whatever the MCP returned.
    """
    if isinstance(payload, list):
        payload = {"data": payload}
    return normalize_payload(payload, cabin)


def normalize_payload(payload: dict, want: Cabin) -> list[Availability]:
    out: list[Availability] = []
    for row in payload.get("data", []):
        route = row.get("Route", {}) if isinstance(row.get("Route"), dict) else {}
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
            fees = _cents_to_usd(row.get(f"{prefix}TotalTaxes"))
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


def _cents_to_usd(v) -> float | None:
    """seats.aero reports TotalTaxes in cents; convert to dollars."""
    i = _to_int(v)
    if i is None:
        return None
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
