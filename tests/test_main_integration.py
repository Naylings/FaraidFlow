import flet as ft

from main import main
from fakes import FakePage


def _children(control):
    items = list(getattr(control, "controls", None) or [])
    for attr in ("content", "label"):
        child = getattr(control, attr, None)
        if child is not None and isinstance(child, ft.Control):
            items.append(child)
    return items


def _find_by_key(control, key):
    if getattr(control, "key", None) == key:
        return control
    for c in _children(control):
        found = _find_by_key(c, key)
        if found is not None:
            return found
    return None


def _find_first(control, ctype):
    if isinstance(control, ctype):
        return control
    for c in _children(control):
        found = _find_first(c, ctype)
        if found is not None:
            return found
    return None


async def _pick_language_id(page):
    page.appbar.actions[0].on_click(None)
    id_tile = page.dialogs[0].content.controls[1]
    await id_tile.on_click(None)


async def test_language_switch_keeps_calculator_and_state():
    page = FakePage()
    await main(page)
    assert _find_by_key(page.controls[0], "menu-calculate") is not None
    _find_by_key(page.controls[0], "menu-calculate").on_click(None)
    gross = _find_by_key(page.controls[0], "estate-gross")
    assert gross is not None
    gross.value = "5000000"
    await _pick_language_id(page)
    assert page.appbar.actions[0].content == "🇮🇩 ID"
    root = page.controls[0]
    assert _find_by_key(root, "menu-calculate") is None
    new_gross = _find_by_key(root, "estate-gross")
    assert new_gross is not None
    assert new_gross.value == "5000000"


async def test_language_switch_on_home_rerenders_home():
    page = FakePage()
    await main(page)
    await _pick_language_id(page)
    assert page.appbar.actions[0].content == "🇮🇩 ID"
    btn = _find_by_key(page.controls[0], "menu-calculate")
    assert btn is not None
    assert btn.content == "Hitung"


async def test_back_to_home_renders_current_language():
    page = FakePage()
    await main(page)
    _find_by_key(page.controls[0], "menu-calculate").on_click(None)
    await _pick_language_id(page)
    calc_root = page.controls[0]
    back_btn = _find_by_key(calc_root, "back-home")
    assert back_btn is not None
    back_btn.on_click(None)
    assert page.appbar.actions[0].content == "🇮🇩 ID"
    btn = _find_by_key(page.controls[0], "menu-calculate")
    assert btn is not None
    assert btn.content == "Hitung"


async def test_calculator_result_survives_language_switch():
    page = FakePage()
    await main(page)
    _find_by_key(page.controls[0], "menu-calculate").on_click(None)
    calc_root = page.controls[0]
    _find_by_key(calc_root, "estate-gross").value = "6000000"
    _find_first(calc_root, ft.RadioGroup).value = "husband"
    _find_by_key(calc_root, "btn-calculate").on_click(None)
    assert _find_by_key(calc_root, "result-table") is not None
    await _pick_language_id(page)
    root = page.controls[0]
    assert _find_by_key(root, "result-table") is not None