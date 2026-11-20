"""Tests for the corrected free-first source behavior (no network)."""

import pytest

from th_monitor.models import Cabin
from th_monitor.source import (
    KeylessPathUnavailable,
    SeatsAeroSource,
    from_mcp_json,
)


def test_no_key_does_not_call_partner_api():
    """Without a key, search must NOT attempt the auth-required Partner API.

    It raises KeylessPathUnavailable pointing at the MCP path instead of making
    a call that always returns 401.
    """
    src = SeatsAeroSource(api_key=None)
    assert src.has_key is False
    with pytest.raises(KeylessPathUnavailable) as e:
        src.search("SSA", "YQR", "2026-12-22", "2026-12-25", Cabin.ECONOMY)
    msg = str(e.value).lower()
    assert "mcp" in msg and "no keyless rest" in msg


def test_from_mcp_json_partner_shape():
    payload = {
        "data": [
            {
                "Route": {"OriginAirport": "SFO", "DestinationAirport": "NRT"},
                "Source": "virgin_atlantic_flying_club",
                "Date": "2026-12-10",
                "ComputedLastSeen": "2026-12-09T00:00:00Z",
                "JAvailable": True,
                "JMileageCost": "52500",
                "JTotalTaxes": "10000",
                "JRemainingSeats": "2",
                "JAirlines": "ANA",
            }
        ]
    }
    avails = from_mcp_json(payload, Cabin.BUSINESS)
    assert len(avails) == 1
    a = avails[0]
    assert a.origin == "SFO" and a.destination == "NRT"
    assert a.miles_cost == 52500
    assert a.cash_fees_usd == 100.0  # 10000 cents -> $100
    assert a.seats == 2
    assert a.operating_carrier == "ANA"


def test_from_mcp_json_bare_list_and_cabin_filter():
    rows = [
        {"OriginAirport": "JFK", "DestinationAirport": "MAD", "Source": "iberia_avios",
         "Date": "2026-12-05", "YAvailable": True, "YMileageCost": "34000",
         "YTotalTaxes": "9000", "YRemainingSeats": "4", "YAirlines": "Iberia"},
    ]
    # Asking for business should filter out the economy-only row.
    assert from_mcp_json(rows, Cabin.BUSINESS) == []
    econ = from_mcp_json(rows, Cabin.ECONOMY)
    assert len(econ) == 1 and econ[0].program == "iberia_avios"
