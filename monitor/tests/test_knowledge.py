"""Tests for the knowledge-base accessor against the repo's real data files."""

from pathlib import Path

from th_monitor.knowledge import Knowledge, _apply_ratio

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _kb() -> Knowledge:
    return Knowledge(DATA_DIR)


def test_loads_all_files():
    kb = _kb()
    assert kb.alliances and kb.partner_awards and kb.sweet_spots
    assert kb.transfer_partners and kb.points_valuations


def test_program_valuation_known_and_unknown():
    kb = _kb()
    v = kb.program_valuation("virgin_atlantic_flying_club")
    assert v is not None and v[0] <= v[1]
    assert kb.program_valuation("not_a_real_program") is None


def test_apply_ratio():
    assert _apply_ratio(145000, "1:1") == 145000
    assert _apply_ratio(100000, "1:2") == 200000
    assert _apply_ratio(100000, "2:1") == 50000
    assert _apply_ratio(100000, "bad") == 0


def test_transfer_options_finds_paths():
    kb = _kb()
    # Chase UR transfers 1:1 to United; holding 145k should surface ~145k.
    opts = kb.transfer_options("united_mileageplus", {"chase_ultimate_rewards": 145000})
    assert 145000 in opts


def test_booking_programs_for_carrier():
    kb = _kb()
    progs = kb.booking_programs_for("United")  # Star Alliance carrier
    assert any("aeroplan" in p or "united" in p or "avianca" in p for p in progs)
