from app.calculation.estate import Estate


def test_net_after_all_deductions():
    e = Estate(gross=600_000_000, funeral=20_000_000, debts=100_000_000, wasiat=30_000_000)
    assert e.net == 450_000_000
    assert e.has_numbers


def test_unpaid_debt_when_estate_cannot_cover():
    e = Estate(gross=100_000_000, funeral=10_000_000, debts=120_000_000)
    assert e.unpaid == 30_000_000
    assert e.net == 0


def test_unpaid_debt_zero_when_covered():
    e = Estate(gross=100_000_000, funeral=10_000_000, debts=60_000_000)
    assert e.unpaid == 0
    assert e.net == 30_000_000


def test_wasiat_cap_and_excess():
    base = 600_000_000 - 20_000_000 - 100_000_000
    e = Estate(gross=600_000_000, funeral=20_000_000, debts=100_000_000, wasiat=200_000_000)
    assert e.wasiat_cap == base // 3
    assert e.wasiat_excess == 200_000_000 - e.wasiat_cap
    assert not e.wasiat_ok


def test_wasiat_ok_within_cap():
    base = 600_000_000 - 20_000_000 - 100_000_000
    e = Estate(gross=600_000_000, funeral=20_000_000, debts=100_000_000, wasiat=base // 3)
    assert e.wasiat_ok


def test_wasiat_larger_than_threshold_is_not_ok_even_floor_equal():
    e = Estate(gross=30, funeral=0, debts=0, wasiat=10)
    assert e.wasiat_cap == 10
    assert e.wasiat_ok is True
    e2 = Estate(gross=30, funeral=0, debts=0, wasiat=11)
    assert e2.wasiat_ok is False
    assert e2.wasiat_excess == 1


def test_when_base_zero_any_wasiat_not_ok():
    e = Estate(gross=10, funeral=10, debts=0, wasiat=1)
    assert e.net == 0
    assert e.wasiat_ok is False


def test_fractions_only_when_no_numbers():
    e = Estate()
    assert not e.has_numbers
    assert e.net == 0
    assert e.unpaid == 0