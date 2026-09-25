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


async def test_each_column_hidden_when_all_single():
    calc, pg, _ = await _page()
    calc.heirs = {"son": 1}
    calc.estate = estate_mod.Estate(gross=60000000)
    calc._compute()
    result = calc._build_result()
    table = _by_key(result, "result-table")
    assert table is not None
    headers = [c.label.value for c in table.columns]
    assert "Each" not in headers


async def test_each_column_shown_when_multiple():
    calc, pg, _ = await _page()
    calc.heirs = {"son": 2}
    calc.estate = estate_mod.Estate(gross=90000000)
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    headers = [c.label.value for c in table.columns]
    assert headers[-3:] == ["Share", "Each", "Total"]


async def test_amounts_display_with_dollar_and_two_decimals():
    calc, pg, _ = await _page()
    calc.heirs = {"daughter": 1}
    calc.estate = estate_mod.Estate(gross=100)
    calc._compute()
    cells = [c.content.value for c in _walk(calc._build_result()) if isinstance(c, ft.DataCell)]
    assert any("$" in v for v in cells)