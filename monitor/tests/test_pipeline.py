"""Pipeline tests using synthetic availability (no network)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from th_monitor.knowledge import Knowledge
from th_monitor.models import Availability, Cabin
from th_monitor.pipeline import evaluate

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _avail(program, carrier, cabin, miles, fees, seats, hours_old=1):
    return Availability(
        origin="SFO", destination="NRT", date="2026-12-10",
        program=program, operating_carrier=carrier, cabin=cabin,
        miles_cost=miles, cash_fees_usd=fees, seats=seats,
        source="seats_aero",
        last_seen=datetime.now(timezone.utc) - timedelta(hours=hours_old),
    )


def test_high_value_opportunity_surfaces_with_cash():
    kb = Knowledge(DATA_DIR)
    a = _avail("virgin_atlantic_flying_club", "ANA", Cabin.BUSINESS, 52500, 100.0, 2)
    cash = {"SFO-NRT|2026-12-10|business": 3000.0}  # strong cash -> high CPM
    opps = evaluate([a], kb, cash_prices=cash)
    assert len(opps) == 1
    assert opps[0].cpm and opps[0].cpm > 1.0
    # ANA business via Virgin is a seeded sweet spot.
    assert opps[0].sweet_spot_id == "va-ana-japan-business"


def test_min_seats_filter():
    kb = Knowledge(DATA_DIR)
    a = _avail("virgin_atlantic_flying_club", "ANA", Cabin.BUSINESS, 52500, 100.0, 1)
    opps = evaluate([a], kb, min_seats=2, cash_prices={"SFO-NRT|2026-12-10|business": 3000.0})
    assert opps == []


def test_reachability_gate_with_transfer():
    kb = Knowledge(DATA_DIR)
    a = _avail("united_mileageplus", "United", Cabin.BUSINESS, 80000, 25.0, 2)
    cash = {"SFO-NRT|2026-12-10|business": 2000.0}
    # 0 direct United, but 100k Chase UR transfers 1:1 -> reachable.
    opps = evaluate([a], kb, held_currencies={"chase_ultimate_rewards": 100000},
                    direct_balances={}, cash_prices=cash, only_high_value=False)
    assert len(opps) == 1 and opps[0].reachable

    # Only 50k Chase UR -> not enough -> dropped.
    opps2 = evaluate([a], kb, held_currencies={"chase_ultimate_rewards": 50000},
                     direct_balances={}, cash_prices=cash, only_high_value=False)
    assert opps2 == []


def test_stale_data_flags_verification():
    kb = Knowledge(DATA_DIR)
    a = _avail("virgin_atlantic_flying_club", "ANA", Cabin.BUSINESS, 52500, 100.0, 2, hours_old=48)
    opps = evaluate([a], kb, cash_prices={"SFO-NRT|2026-12-10|business": 3000.0})
    assert opps[0].needs_verification
    assert any("verify" in n for n in opps[0].notes)


def test_no_cash_marks_incomplete():
    kb = Knowledge(DATA_DIR)
    a = _avail("virgin_atlantic_flying_club", "ANA", Cabin.BUSINESS, 52500, 100.0, 2)
    opps = evaluate([a], kb, cash_prices={})  # no cash
    # still surfaces because it's a sweet spot, but flagged incomplete
    assert opps[0].cash_price_available is False
    assert any("cash price unavailable" in n for n in opps[0].notes)
