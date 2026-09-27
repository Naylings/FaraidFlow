import flet as ft

from app.calculation import estate as estate_mod
from app.localization.localization import Localization
from app.pages.calculate import CalculationPage
from fakes import FakePage, FakeStorage


async def _page(language="en"):
    loc = await Localization.load(FakeStorage(), default_language="en")
    pg = FakePage()
    calc = CalculationPage(pg, loc, back_home=lambda: None)
    return calc, pg, loc


def _children(control):
    items = list(getattr(control, "controls", None) or [])
    for attr in ("rows", "columns", "cells"):
        children = getattr(control, attr, None)
        if isinstance(children, list):
            for child in children:
                if isinstance(child, ft.Control):
                    items.append(child)
    for attr in ("content", "label"):
        child = getattr(control, attr, None)
        if child is not None and isinstance(child, ft.Control):
            items.append(child)
    return items


def _walk(control):
    yield control
    for c in _children(control):
        yield from _walk(c)


def _by_key(control, key):
    if getattr(control, "key", None) == key:
        return control
    for c in _children(control):
        found = _by_key(c, key)
        if found is not None:
            return found
    return None


def _buttons(calc):
    return [c for c in _walk(calc.build()) if isinstance(c, ft.FilledButton)]


async def test_form_build_contains_estate_fields_and_calculate():
    calc, pg, _ = await _page()
    root = calc.build()
    assert _by_key(root, "estate-gross") is not None
    assert _by_key(root, "estate-funeral") is not None
    assert _by_key(root, "estate-debts") is not None
    assert _by_key(root, "estate-wasiat") is not None
    assert _by_key(root, "btn-calculate") is not None


async def test_calculate_produces_result_rows():
    calc, pg, _ = await _page()
    calc.heirs = {"son": 1, "daughter": 1}
    calc._compute()
    assert calc.calc_result is not None
    assert {r.key for r in calc.calc_result.rows} == {"son", "daughter"}


async def test_fractions_only_when_no_numbers():
    calc, pg, _ = await _page()
    calc.heirs = {"son": 1, "father": 1}
    calc._compute()
    assert calc.calc_result.rows[0].amount is None


async def test_result_card_shows_breakdown_with_wasiat():
    calc, pg, loc = await _page()
    from app.calculation.estate import Estate

    calc.heirs = {"daughter": 1, "father": 1}
    calc.estate = Estate(gross=600_000_000, funeral=20_000_000, debts=100_000_000, wasiat=30_000_000)
    calc._compute()
    texts = [c.value for c in _walk(calc._build_result()) if isinstance(c, ft.Text)]
    assert any(t and loc.get("calc.wasiat") in t for t in texts)


async def test_tree_shows_deceased_and_selected_branches():
    calc, pg, loc = await _page()
    calc.heirs = {"son": 2, "daughter": 1}
    calc.estate = estate_mod.Estate()
    calc._compute()
    texts = [c.value for c in _walk(calc.build()) if isinstance(c, ft.Text)]
    assert "Deceased" in texts or loc.get("calc.deceased") in texts
    assert "Son" in texts


async def test_form_estate_fields_are_numeric_and_page_scrolls():
    calc, pg, _ = await _page()
    root = calc.build()
    assert getattr(root, "scroll", None) == ft.ScrollMode.AUTO
    assert getattr(root, "expand", None) is True
    for key in ("estate-gross", "estate-funeral", "estate-debts", "estate-wasiat"):
        tf = _by_key(root, key)
        assert tf is not None
        assert getattr(tf, "keyboard_type", None) == ft.KeyboardType.NUMBER
        assert getattr(tf, "input_filter", None) is not None
        assert isinstance(getattr(tf, "input_filter", None), ft.InputFilter)
    card_col = _by_key(root, "col-cards")
    assert card_col is not None
    assert getattr(card_col, "horizontal_alignment", None) == ft.CrossAxisAlignment.STRETCH


async def test_estate_field_groups_input_commas():
    calc, pg, _ = await _page()
    root = calc.build()
    gross = _by_key(root, "estate-gross")
    assert gross is not None
    gross.value = "5000000"
    calc._collect()
    assert calc.estate.gross == 5000000


async def test_estate_input_accepts_commas_and_strips_on_parse():
    calc, pg, _ = await _page()
    root = calc.build()
    calc._tf["estate-gross"].value = "12,345,678"
    calc._collect()
    assert calc.estate.gross == 12345678


async def test_capture_state_none_before_build():
    calc, _, _ = await _page()
    assert calc.capture_state() is None


async def test_restore_state_none_is_noop():
    calc, _, _ = await _page()
    calc.build()
    calc.restore_state(None)
    assert calc.capture_state()["has_result"] is False


async def test_capture_restore_round_trip_preserves_state():
    calc, _, _ = await _page()
    calc.build()
    calc._tf["estate-gross"].value = "5,000,000"
    calc._spouse.value = "wife"
    calc._wife_count.value = "2"
    calc._count_fields["daughter"].value = "2"
    calc._parent_checkboxes["father"].value = True
    state = calc.capture_state()
    assert state["tf"]["estate-gross"] == "5,000,000"
    assert state["spouse"] == "wife"
    assert state["counts"]["daughter"] == "2"
    assert state["parents"]["father"] is True
    assert state["has_result"] is False
    calc.build()
    calc.restore_state(state)
    assert calc._tf["estate-gross"].value == "5,000,000"
    assert calc._spouse.value == "wife"
    assert calc._count_fields["daughter"].value == "2"
    assert calc._parent_checkboxes["father"].value is True


async def test_restore_state_regenerates_result_in_new_language():
    calc, _, loc = await _page("en")
    calc.build()
    calc._tf["estate-gross"].value = "6000000"
    calc._spouse.value = "husband"
    calc._count_fields["daughter"].value = "1"
    calc._collect()
    calc._compute()
    state = calc.capture_state()
    assert state["has_result"] is True
    assert _by_key(calc.build(), "result-table") is not None
    await loc.set_language("id")
    calc.build()
    calc.restore_state(state)
    texts = [c.value for c in _walk(calc.result_card) if isinstance(c, ft.Text)]
    assert any("Suami" in (v or "") for v in texts)


from app.pages.calculate import _fmt_int, _money


def test_fmt_int_groups_thousands():
    assert _fmt_int(5000000) == "5,000,000"
    assert _fmt_int(0) == "0"


def test_parse_int_strips_commas():
    from app.pages.calculate import _parse_int
    assert _parse_int("12,345") == 12345
    assert _parse_int("") == 0
    assert _parse_int("abc") == 0


def test_money_formats_en():
    from decimal import Decimal
    t = {"money.prefix": "$", "money.thousands_sep": ",", "money.decimal_sep": "."}.get
    assert _money(Decimal("1234567.89"), t) == "$1,234,567.89"


def test_money_formats_id():
    from decimal import Decimal
    t = {"money.prefix": "$", "money.thousands_sep": ".", "money.decimal_sep": ","}.get
    assert _money(Decimal("1234567.89"), t) == "$1.234.567,89"


async def test_wife_count_disabled_by_default_and_enabled_on_wife():
    calc, pg, _ = await _page()
    root = calc.build()
    wife = _by_key(root, "count-wife")
    assert wife is not None
    assert wife.disabled is True
    calc._spouse.value = "wife"
    calc._spouse.on_change(None)
    assert calc._wife_count.disabled is False


async def test_parents_are_checkboxes_without_count_fields():
    calc, pg, _ = await _page()
    root = calc.build()
    checks = [c for c in _walk(root) if isinstance(c, ft.Checkbox)]
    assert {c.key for c in checks} >= {"father", "mother"}
    assert "father" not in calc._count_fields
    assert "mother" not in calc._count_fields


async def test_heir_counts_are_number_fields_not_dropdowns():
    calc, pg, _ = await _page()
    root = calc.build()
    for key in ("son", "daughter", "brother_full", "sister_uterine"):
        field = _by_key(root, f"count-{key}")
        assert field is not None
        assert isinstance(field, ft.TextField)
        assert not isinstance(field, ft.Dropdown)


HEIR_COUNT_KEYS = (
    "son", "daughter",
    "brother_full", "sister_full",
    "brother_consang", "sister_consang",
    "brother_uterine", "sister_uterine",
)


async def test_heir_counts_prefilled_with_zero_like_the_estate_fields():
    calc, pg, _ = await _page()
    root = calc.build()
    for key in HEIR_COUNT_KEYS:
        field = _by_key(root, f"count-{key}")
        assert field is not None, key
        assert field.value == "0", key
    # the estate block already defaulted to "0"; the form must now match it
    for key in ("estate-gross", "estate-funeral", "estate-debts", "estate-wasiat"):
        assert _by_key(root, key).value == "0", key


async def test_untouched_form_with_zero_counts_shows_no_heirs_error():
    calc, pg, _ = await _page()
    calc.build()
    calc._collect()
    calc._compute()
    assert calc.calc_result.errors == ["calc.errors.no_heirs"]
    assert calc.calc_result.rows == []
    assert calc._wife_count.value == "1"


async def test_each_column_hidden_when_all_single():
    calc, pg, _ = await _page()
    calc.heirs = {"son": 1}
    calc.estate = estate_mod.Estate(gross=60000000)
    calc._compute()
    result = calc._build_result()
    table = _by_key(result, "result-table")
    assert table is not None
    headers = [c.value for c in table.controls[0].controls]
    assert "Each" not in headers


async def test_each_column_shown_when_multiple():
    calc, pg, _ = await _page()
    calc.heirs = {"son": 2}
    calc.estate = estate_mod.Estate(gross=90000000)
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    headers = [c.value for c in table.controls[0].controls]
    assert headers[-3:] == ["Share", "Each", "Total"]


async def test_amounts_display_with_dollar_and_two_decimals():
    calc, pg, _ = await _page()
    calc.heirs = {"daughter": 1}
    calc.estate = estate_mod.Estate(gross=100)
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    cells = [c.value for row in table.controls[2:] for c in row.controls]
    assert any("$" in v for v in cells)


async def test_share_column_shows_group_share_not_per_person_share():
    # Wife + 2 sons: wife 1/8, sons share 7/8 between them.
    # The row is labelled "Son x2" and its Total is the whole group total,
    # so the Share cell must be the group share (7/8), not the per-person 7/16.
    calc, pg, _ = await _page()
    calc.heirs = {"wife": 1, "son": 2}
    calc.estate = estate_mod.Estate(gross=1000)
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    rows = {r.controls[0].value: [c.value for c in r.controls] for r in table.controls[2:]}
    assert rows["Son  x2"][1] == "7/8"
    assert rows["Wife"][1] == "1/8"
    # per-person share 7/16 must not leak into the table
    assert all(v[1] != "7/16" for v in rows.values())


async def test_share_column_matches_total_column_basis_for_groups():
    calc, pg, _ = await _page()
    calc.heirs = {"son": 3}
    calc.estate = estate_mod.Estate(gross=9000)
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    row = [c.value for c in table.controls[2].controls]
    # group share 1 -> share cell "1", each 3000, total 9000
    assert row[1] == "1"
    assert row[2] == "$3,000.00"
    assert row[3] == "$9,000.00"


async def test_result_table_cells_expand_to_fill_container():
    calc, pg, _ = await _page()
    calc.heirs = {"son": 2, "daughter": 1}
    calc.estate = estate_mod.Estate(gross=100)
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    assert table is not None
    for row in table.controls:
        if not isinstance(row, ft.Row):
            continue
        assert all(c.expand for c in row.controls), "every cell must expand"
    assert sum(c.expand for c in table.controls[0].controls) > 0


async def test_result_table_expands_with_and_without_each_column():
    calc, pg, _ = await _page()
    calc.estate = estate_mod.Estate(gross=100)
    calc.heirs = {"son": 2}
    calc._compute()
    with_each = _by_key(calc._build_result(), "result-table")
    calc.heirs = {"son": 1}
    calc._compute()
    without_each = _by_key(calc._build_result(), "result-table")
    assert len(with_each.controls[0].controls) == 4
    assert len(without_each.controls[0].controls) == 3
    for table in (with_each, without_each):
        assert all(c.expand for c in table.controls[0].controls)
        for row in table.controls[2:]:
            assert all(c.expand for c in row.controls)


async def test_debt_note_only_when_unpaid():
    calc, pg, loc = await _page()
    calc.heirs = {"son": 1}
    calc.estate = estate_mod.Estate(gross=100, funeral=10, debts=20)
    calc._compute()
    texts = [c.value for c in _walk(calc._build_result()) if isinstance(c, ft.Text)]
    assert not any(t and "Debts are not inherited" in t for t in texts)


async def test_debt_note_shown_when_unpaid():
    calc, pg, loc = await _page()
    calc.heirs = {"son": 1}
    calc.estate = estate_mod.Estate(gross=100, funeral=10, debts=120)
    calc._compute()
    texts = [c.value for c in _walk(calc._build_result()) if isinstance(c, ft.Text)]
    assert any(t and "Debts are not inherited" in t for t in texts)


async def test_no_heirs_error_suppresses_others():
    calc, pg, _ = await _page()
    calc.heirs = {}
    calc.estate = estate_mod.Estate(gross=100)
    calc._compute()
    errs = [c.value for c in _walk(calc._build_result()) if isinstance(c, ft.Text) and c.color == ft.Colors.ERROR]
    assert errs == ["Select at least one heir."]


async def test_section_headings_localize_in_id():
    loc = await Localization.load(FakeStorage(), default_language="en")
    await loc.set_language("id")
    pg = FakePage()
    calc = CalculationPage(pg, loc, back_home=lambda: None)
    root = calc.build()
    texts = [c.value for c in _walk(root) if isinstance(c, ft.Text)]
    assert "Anak" in texts
    assert "Orang Tua" in texts
    assert "Saudara" in texts


from fractions import Fraction as F


def test_equivalence_lines_from_group_shares():
    from app.calculation.engine import Row
    from app.pages.calculate import _equivalence_lines
    rows = [
        Row(key="husband", count=1, share=F(1, 2)),
        Row(key="father", count=1, share=F(1, 3)),
        Row(key="mother", count=1, share=F(1, 6)),
    ]
    lines = _equivalence_lines(rows)
    assert lines == ["1/2 = 3/6", "1/3 = 2/6", "1/6 = 1/6"]


async def test_tree_marks_blocked_sibling_disabled():
    calc, pg, _ = await _page()
    calc.heirs = {"brother_full": 1, "brother_consang": 1}
    calc.estate = estate_mod.Estate()
    calc._compute()
    root = calc.build()
    chips = [c for c in _walk(root) if isinstance(c, ft.Chip) and c.label.value.startswith("Paternal")]
    assert chips
    assert all(chip.disabled for chip in chips)
    assert all(chip.tooltip is not None for chip in chips)


def test_equivalence_lines_use_group_share_so_sum_to_one():
    from app.calculation.engine import Row
    from app.pages.calculate import _equivalence_lines
    rows = [
        Row(key="son", count=2, share=F(1, 5)),     # per person
        Row(key="daughter", count=1, share=F(1, 5)),
    ]
    lines = _equivalence_lines(rows)
    # group shares: 2/5 and 1/5 -> lcm 5 -> "2/5 = 2/5", "1/5 = 1/5"
    assert lines == ["2/5 = 2/5", "1/5 = 1/5"]


async def test_result_card_uses_scroll_key_so_scroll_to_can_find_it():
    calc, pg, _ = await _page()
    calc.build()
    key = calc.result_card.key
    assert isinstance(key, ft.ScrollKey)
    assert str(key) == "result-card"


async def test_wife_count_is_a_dropdown_limited_to_one_through_four():
    calc, pg, _ = await _page()
    calc.build()
    wife = calc._wife_count
    assert isinstance(wife, ft.Dropdown)
    assert [o.key for o in wife.options] == ["1", "2", "3", "4"]
    assert wife.value == "1"
    assert wife.editable is not True


async def test_wife_count_dropdown_feeds_slot_and_defaults_to_one():
    calc, pg, _ = await _page()
    calc.build()
    calc._spouse.value = "wife"
    calc._sync_wife_count()
    assert calc._wife_count.disabled is False
    assert calc._slot_from_inputs() == {"wife": 1}
    calc._wife_count.value = "4"
    assert calc._slot_from_inputs() == {"wife": 4}
    calc._spouse.value = "none"
    calc._sync_wife_count()
    assert calc._wife_count.disabled is True
    assert "wife" not in calc._slot_from_inputs()


async def test_wife_count_empty_or_zero_falls_back_to_one():
    calc, pg, _ = await _page()
    calc.build()
    calc._spouse.value = "wife"
    for bad in ("", "0", None):
        calc._wife_count.value = bad
        assert calc._slot_from_inputs() == {"wife": 1}