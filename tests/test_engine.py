from fractions import Fraction

import pytest

from app.calculation.engine import resolve
from app.calculation.estate import Estate

F = Fraction


def shares_of(r, key):
    row = next(x for x in r.rows if x.key == key)
    return row.share, row.count, row.amount


def total_shares(r):
    return sum(row.share * row.count for row in r.rows)


# --- the 16 fixtures from docs/faraid-calculator-rules.md §10 ---

def test_f1_husband_father_mother():
    r = resolve({"husband": 1, "father": 1, "mother": 1})
    assert shares_of(r, "husband")[0] == F(1, 2)
    assert shares_of(r, "mother")[0] == F(1, 6)     # 1/3 of remainder
    assert shares_of(r, "father")[0] == F(1, 3)     # residue
    assert r.asabah_keys == ["father"]
    assert r.radd_applied is False


def test_f2_wife_father_mother():
    r = resolve({"wife": 1, "father": 1, "mother": 1})
    assert shares_of(r, "wife")[0] == F(1, 4)
    assert shares_of(r, "mother")[0] == F(1, 4)     # 1/3 of 3/4
    assert shares_of(r, "father")[0] == F(1, 2)


def test_f3_husband_mother_radd():
    r = resolve({"husband": 1, "mother": 1})
    assert shares_of(r, "husband")[0] == F(1, 2)
    assert shares_of(r, "mother")[0] == F(1, 2)     # 1/3 + ridded 1/6
    assert r.radd_applied is True


def test_f4_aul_wife_2daughters_parents():
    r = resolve({"wife": 1, "daughter": 2, "mother": 1, "father": 1})
    assert r.aul is True
    assert r.base_from == 24
    assert r.base == 27
    assert shares_of(r, "wife")[0] == F(3, 27)
    assert shares_of(r, "daughter")[0] == F(8, 27)  # 16/27 shared → per person
    assert shares_of(r, "mother")[0] == F(4, 27)
    assert shares_of(r, "father")[0] == F(4, 27)


def test_f5_son_2daughters_asabah_2to1():
    r = resolve({"son": 1, "daughter": 2})
    assert shares_of(r, "son")[0] == F(1, 2)
    assert shares_of(r, "daughter")[0] == F(1, 4)
    assert r.asabah_keys == ["son", "daughter"]


def test_f6_daughter_father():
    r = resolve({"daughter": 1, "father": 1})
    assert shares_of(r, "daughter")[0] == F(1, 2)
    assert shares_of(r, "father")[0] == F(1, 2)     # 1/6 + residue 1/3


def test_f7_wife_2daughters_full_sister_asabah():
    r = resolve({"wife": 1, "daughter": 2, "sister_full": 1})
    assert shares_of(r, "wife")[0] == F(1, 8)
    assert shares_of(r, "daughter")[0] == F(1, 3)   # 2/3 shared
    assert shares_of(r, "sister_full")[0] == F(5, 24)
    assert r.asabah_keys == ["sister_full"]


def test_f8_wife_2full_sisters_radd():
    r = resolve({"wife": 1, "sister_full": 2})
    assert shares_of(r, "wife")[0] == F(1, 4)
    assert shares_of(r, "sister_full")[0] == F(3, 8)
    assert r.radd_applied is True


def test_f9_mother_single_daughter_radd():
    r = resolve({"mother": 1, "daughter": 1})
    assert r.radd_applied is True
    assert shares_of(r, "daughter")[0] == F(3, 4)
    assert shares_of(r, "mother")[0] == F(1, 4)


def test_f10_wife_only_unassigned():
    r = resolve({"wife": 1})
    assert shares_of(r, "wife")[0] == F(1, 4)
    assert r.unassigned == F(3, 4)
    assert r.radd_applied is False
    assert total_shares(r) == F(1, 4)


def test_f11_full_brother_alone():
    r = resolve({"brother_full": 1})
    assert shares_of(r, "brother_full")[0] == F(1, 1)
    assert r.asabah_keys == ["brother_full"]


def test_f12_son_father_wife_mother():
    r = resolve({"son": 1, "father": 1, "wife": 1, "mother": 1})
    assert shares_of(r, "wife")[0] == F(1, 8)
    assert shares_of(r, "mother")[0] == F(1, 6)
    assert shares_of(r, "father")[0] == F(1, 6)
    assert shares_of(r, "son")[0] == F(13, 24)


def test_f13_two_uterine_brothers():
    r = resolve({"brother_uterine": 2})
    assert shares_of(r, "brother_uterine")[0] == F(1, 2)  # radd: each 1/2
    assert r.radd_applied is True
    assert r.base_from == 3


def test_f14_full_sister_consang_sister():
    r = resolve({"sister_full": 1, "sister_consang": 1})
    assert shares_of(r, "sister_full")[0] == F(3, 4)
    assert shares_of(r, "sister_consang")[0] == F(1, 4)
    assert r.radd_applied is True


def test_f15_two_full_sisters_consang_excluded():
    r = resolve({"sister_full": 2, "sister_consang": 1})
    assert "sister_consang" not in [x.key for x in r.rows]
    assert shares_of(r, "sister_full")[0] == F(1, 2)


def test_f16_wife_2daughters_father():
    r = resolve({"wife": 1, "daughter": 2, "father": 1})
    assert shares_of(r, "wife")[0] == F(1, 8)
    assert shares_of(r, "daughter")[0] == F(1, 3)
    assert shares_of(r, "father")[0] == F(5, 24)


# --- blocking, amounts, estates, errors ---

def test_blocked_sibling_omitted_and_listed():
    r = resolve({"son": 1, "sister_full": 1})
    assert [x.key for x in r.rows] == ["son"]
    assert r.blocked_keys == ["sister_full"]


def test_amounts_are_net_times_group_share():
    e = Estate(gross=450_000_000)
    r = resolve({"wife": 1, "daughter": 2, "father": 1}, estate=e)
    row_wife = next(x for x in r.rows if x.key == "wife")
    assert row_wife.amount == Decimal("450000000") * Decimal("0.125")   # 1/8
    row_d = next(x for x in r.rows if x.key == "daughter")
    assert row_d.amount == Decimal("450000000") * Decimal(2) / Decimal(3)


def test_no_numbers_means_no_amounts():
    r = resolve({"son": 1})
    assert all(x.amount is None for x in r.rows)


def test_errors_returned_when_invalid():
    r = resolve({"husband": 1, "wife": 1, "son": 1})
    assert r.errors == ["calc.errors.spouse_both"]
    assert r.rows == []


def test_errors_returned_empty_heirs():
    r = resolve({})
    assert r.errors == ["calc.errors.no_heirs"]


@pytest.mark.parametrize("heirs", [
    {"husband": 1, "father": 1, "mother": 1},
    {"wife": 1, "daughter": 2, "mother": 1, "father": 1},
    {"son": 2, "daughter": 3},
    {"wife": 1, "sister_full": 2},
    {"mother": 1, "daughter": 1},
    {"wife": 1, "sister_full": 1, "sister_consang": 1},
])
def test_property_shares_sum_to_one_or_residue_notes(heirs):
    r = resolve(heirs)
    assert not r.errors
    s = total_shares(r)
    gap = F(1, 1) - s
    assert gap >= 0
    if r.unassigned is not None:
        assert gap == r.unassigned
    else:
        assert gap == 0
    assert all(x.share >= 0 for x in r.rows)


from decimal import Decimal


def _quant(value):
    return value.quantize(Decimal("0.01"))


def test_amounts_and_each_are_two_decimal_decimals():
    e = Estate(gross=450_000_000)
    r = resolve({"wife": 1, "daughter": 2, "father": 1}, estate=e)
    row_wife = next(x for x in r.rows if x.key == "wife")
    assert row_wife.amount == _quant(Decimal("56250000.00"))
    assert row_wife.each == _quant(Decimal("56250000.00"))   # count == 1
    row_d = next(x for x in r.rows if x.key == "daughter")
    assert row_d.count == 2
    assert row_d.amount == _quant(Decimal("450000000") * Decimal(2) / Decimal(3))
    assert row_d.each == _quant(Decimal("450000000") * Decimal(2) / Decimal(3) / Decimal(2))
    assert row_d.each * 2 <= row_d.amount + Decimal("0.01")


def test_amount_still_none_when_no_estate():
    r = resolve({"son": 1})
    row = r.rows[0]
    assert row.amount is None
    assert row.each is None


def test_residual_zero_when_exact():
    e = Estate(gross=600_000_000)
    r = resolve({"husband": 1, "father": 1, "mother": 1}, estate=e)
    assert r.residual == Decimal("0")


def test_residual_nonzero_when_head_split_leaves_cents():
    e = Estate(gross=100)
    r = resolve({"brother_uterine": 3}, estate=e)
    # 3 uterine brothers share all (radd); each gets 33.33, leaving 0.01
    assert r.residual == Decimal("0.01")