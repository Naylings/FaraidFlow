from app.calculation import heirs


def test_keys_are_exactly_scope_b():
    assert heirs.HEIR_KEYS == [
        "husband", "wife", "son", "daughter", "father", "mother",
        "brother_full", "sister_full", "brother_consang", "sister_consang",
        "brother_uterine", "sister_uterine",
    ]


def test_sections_order_spouse_children_parents_siblings():
    assert [s for s, _ in heirs.HEIR_SECTIONS] == [
        "spouse", "children", "parents", "siblings",
    ]
    assert heirs.HEIR_SECTIONS[3][1] == [
        "brother_full", "sister_full", "brother_consang", "sister_consang",
        "brother_uterine", "sister_uterine",
    ]


def test_normalize_fills_zeros_and_keeps_any_wife_count():
    assert heirs.normalize({"wife": 6, "husband": 3}) == {
        "husband": 1, "wife": 6, "son": 0, "daughter": 0, "father": 0,
        "mother": 0, "brother_full": 0, "sister_full": 0, "brother_consang": 0,
        "sister_consang": 0, "brother_uterine": 0, "sister_uterine": 0,
    }


def test_errors_catch_bad_inputs():
    assert heirs.errors({}) == ["calc.errors.no_heirs"]
    assert heirs.errors({"husband": 1, "wife": 1, "son": 1}) == ["calc.errors.spouse_both"]
    assert heirs.errors({"father": 1}) == []
    assert heirs.errors({"wife": 5}) == []


def test_errors_ok_for_valid():
    assert heirs.errors({"son": 2, "daughter": 1}) == []


def test_normalize_drops_unknown_keys():
    assert heirs.normalize({"son": 1, "cousin": 5})["son"] == 1
    assert "cousin" in heirs.HEIR_KEYS or "cousin" not in heirs.normalize({"cousin": 5})