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
        assert isinstance(getattr(tf, "input_filter", None), ft.NumbersOnlyInputFilter)
    card_col = _by_key(root, "col-cards")
    assert card_col is not None
    assert getattr(card_col, "horizontal_alignment", None) == ft.CrossAxisAlignment.STRETCH