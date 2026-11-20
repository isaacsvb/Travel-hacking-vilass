"""Unit tests for the pure value calculator."""

from th_monitor.calculator import (
    classify_value,
    compute_cpm,
    effective_miles,
    is_high_value,
)
from th_monitor.models import ValueClass


def test_compute_cpm_basic():
    # $1900 cash, $100 fees, 52500 miles -> (1800 * 100) / 52500
    assert compute_cpm(1900.0, 100.0, 52500) == round(180000 / 52500, 3)


def test_compute_cpm_zero_or_none_miles_returns_none():
    assert compute_cpm(1000.0, 50.0, 0) is None
    assert compute_cpm(1000.0, 50.0, None) is None


def test_compute_cpm_includes_fees():
    high_fees = compute_cpm(1000.0, 500.0, 50000)
    low_fees = compute_cpm(1000.0, 50.0, 50000)
    assert high_fees < low_fees  # fees drag CPM down


def test_classify_value_thresholds():
    floor, ceiling = 1.0, 1.4
    assert classify_value(1.5, floor, ceiling) == ValueClass.EXCEPTIONAL
    assert classify_value(1.4, floor, ceiling) == ValueClass.EXCEPTIONAL
    assert classify_value(1.1, floor, ceiling) == ValueClass.GOOD
    assert classify_value(0.8, floor, ceiling) == ValueClass.MEDIOCRE  # >= 0.7
    assert classify_value(0.5, floor, ceiling) == ValueClass.POOR


def test_classify_value_none_is_poor():
    assert classify_value(None, 1.0, 1.4) == ValueClass.POOR


def test_effective_miles_takes_best_single_transfer():
    # direct 16000, can bring 145000 from one currency and 30000 from another
    assert effective_miles(16000, [145000, 30000]) == 161000
    assert effective_miles(0, []) == 0


def test_is_high_value_gate():
    assert is_high_value(ValueClass.GOOD)
    assert is_high_value(ValueClass.EXCEPTIONAL)
    assert not is_high_value(ValueClass.MEDIOCRE)
    assert not is_high_value(ValueClass.POOR)
