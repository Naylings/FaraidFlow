import flet as ft
import pytest

from app.localization.localization import STORAGE_KEYS
from main import main
from fakes import FakePage, FakeStorage


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
    id_tile = _find_by_key(page.dialogs[0], "lang-id")
    await id_tile.on_click(None)


async def _pick_theme(page, code):
    page.appbar.actions[0].on_click(None)
    theme_tile = _find_by_key(page.dialogs[0], f"theme-{code}")
    await theme_tile.on_click(None)


async def _pick_currency(page, code):
    page.appbar.actions[0].on_click(None)
    currency_tile = _find_by_key(page.dialogs[0], f"currency-{code}")
    await currency_tile.on_click(None)


def _result_text(root):
    table = _find_by_key(root, "result-table")
    texts = []
    for row in table.controls:
        for cell in getattr(row, "controls", []) or []:
            value = getattr(cell, "value", None)
            if isinstance(value, str):
                texts.append(value)
    return " ".join(texts)


def _use_storage(monkeypatch, storage):
    """main() builds its own ft.SharedPreferences, which needs a live page
    connection; swap in a fake so a test can seed and inspect what is stored."""
    monkeypatch.setattr(ft, "SharedPreferences", lambda: storage)


def _appbar_action(page, key):
    for action in page.appbar.actions or []:
        if getattr(action, "key", None) == key:
            return action
    return None


def _count_by_key(control, key):
    total = 0
    if getattr(control, "key", None) == key:
        total += 1
    for c in _children(control):
        total += _count_by_key(c, key)
    return total


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


async def test_appbar_calculate_action_exists_only_on_the_calculate_screen():
    page = FakePage()
    await main(page)
    assert _appbar_action(page, "appbar-calculate") is None
    _find_by_key(page.controls[0], "menu-calculate").on_click(None)
    action = _appbar_action(page, "appbar-calculate")
    assert action is not None
    assert page.appbar.actions[0].key == "settings-button", "settings button must stay at index 0"
    assert page.appbar.actions[1] is action
    _find_by_key(page.controls[0], "back-home").on_click(None)
    assert _appbar_action(page, "appbar-calculate") is None


async def test_appbar_calculate_action_matches_the_in_form_button():
    page = FakePage()
    await main(page)
    _find_by_key(page.controls[0], "menu-calculate").on_click(None)
    root = page.controls[0]
    _find_by_key(root, "estate-gross").value = "6000000"
    _find_first(root, ft.RadioGroup).value = "husband"
    action = _appbar_action(page, "appbar-calculate")
    # the in-form button is preserved and still the same sync handler
    in_form = _find_by_key(root, "btn-calculate")
    assert in_form is not None
    assert in_form.on_click == action.on_click
    assert _find_by_key(root, "result-table") is None
    in_form.on_click(None)
    assert _find_by_key(root, "result-table") is not None
    action.on_click(None)
    assert _find_by_key(root, "result-table") is not None


async def test_appbar_calculate_action_survives_a_language_switch():
    page = FakePage()
    await main(page)
    _find_by_key(page.controls[0], "menu-calculate").on_click(None)
    before = _appbar_action(page, "appbar-calculate")
    assert before.tooltip == "Calculate"
    await _pick_language_id(page)
    action = _appbar_action(page, "appbar-calculate")
    assert action is not None
    assert action is not before, "AppBar must be rebuilt, not retained, across the switch"
    assert action.tooltip == "Hitung"
    root = page.controls[0]
    _find_by_key(root, "estate-gross").value = "6000000"
    _find_first(root, ft.RadioGroup).value = "husband"
    action.on_click(None)
    assert _find_by_key(root, "result-table") is not None
    assert _count_by_key(root, "appbar-calculate") == 0  # action lives in the appbar, not the body


async def test_appbar_calculate_action_is_reachable_on_a_long_form():
    page = FakePage()
    await main(page)
    _find_by_key(page.controls[0], "menu-calculate").on_click(None)
    root = page.controls[0]
    for key in ("brother_full", "brother_uterine"):
        _find_by_key(root, f"count-{key}").value = "9"
    _find_by_key(root, "count-son").value = "12"
    action = _appbar_action(page, "appbar-calculate")
    assert action.tooltip == "Calculate"
    action.on_click(None)
    assert _find_by_key(root, "result-table") is not None


async def test_resize_across_the_breakpoint_rebuilds_the_layout():
    page = FakePage()
    page.width = 1400
    await main(page)
    _find_by_key(page.controls[0], "menu-calculate").on_click(None)
    assert page.controls[0].scroll is None
    _find_by_key(page.controls[0], "estate-gross").value = "6000000"

    page.width = 700
    page.on_resize(None)
    assert page.controls[0].scroll == ft.ScrollMode.AUTO
    assert _find_by_key(page.controls[0], "estate-gross").value == "6000000"

    page.width = 1400
    page.on_resize(None)
    assert page.controls[0].scroll is None
    assert _count_by_key(page.controls[0], "estate-gross") == 1, "no duplicated controls"
    assert _count_by_key(page.controls[0], "btn-calculate") == 1
    assert _find_by_key(page.controls[0], "estate-gross").value == "6000000"


async def test_resize_within_one_mode_does_not_rebuild():
    page = FakePage()
    page.width = 1400
    await main(page)
    _find_by_key(page.controls[0], "menu-calculate").on_click(None)
    first = page.controls[0]
    page.width = 1200
    page.on_resize(None)
    assert page.controls[0] is first, "same-mode resize must not rebuild the tree"


async def test_app_starts_in_the_system_theme_when_nothing_is_stored():
    """The theme comes from the stored settings, never from a hardcoded mode."""
    page = FakePage()
    await main(page)
    assert page.theme_mode is ft.ThemeMode.SYSTEM


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("light", ft.ThemeMode.LIGHT),
        ("dark", ft.ThemeMode.DARK),
        ("system", ft.ThemeMode.SYSTEM),
    ],
)
async def test_stored_theme_is_applied_at_startup(monkeypatch, code, expected):
    storage = FakeStorage()
    await storage.set(STORAGE_KEYS["theme"], code)
    _use_storage(monkeypatch, storage)
    page = FakePage()
    await main(page)
    assert page.theme_mode is expected


async def test_selecting_a_theme_updates_the_page(monkeypatch):
    storage = FakeStorage()
    _use_storage(monkeypatch, storage)
    page = FakePage()
    await main(page)
    assert page.theme_mode is ft.ThemeMode.SYSTEM
    await _pick_theme(page, "dark")
    assert page.theme_mode is ft.ThemeMode.DARK
    assert (await storage.get(STORAGE_KEYS["theme"])) == "dark"
    assert page.dialogs == []


async def test_selecting_a_theme_keeps_the_calculator_and_state(monkeypatch):
    _use_storage(monkeypatch, FakeStorage())
    page = FakePage()
    await main(page)
    _find_by_key(page.controls[0], "menu-calculate").on_click(None)
    _find_by_key(page.controls[0], "estate-gross").value = "7000000"
    await _pick_theme(page, "light")
    assert page.theme_mode is ft.ThemeMode.LIGHT
    root = page.controls[0]
    assert _find_by_key(root, "btn-calculate") is not None
    assert _find_by_key(root, "estate-gross").value == "7000000"


async def test_settings_currency_choice_persists_and_reopens_checked(monkeypatch):
    """The brief's settings bullet at main level: open settings, pick a
    currency, it persists and closes; reopening shows it as the checked one."""
    storage = FakeStorage()
    _use_storage(monkeypatch, storage)
    page = FakePage()
    await main(page)
    await _pick_currency(page, "idr")
    assert (await storage.get(STORAGE_KEYS["currency"])) == "IDR"
    assert page.dialogs == []
    page.appbar.actions[0].on_click(None)
    assert _find_by_key(page.dialogs[0], "currency-idr").trailing is not None
    assert _find_by_key(page.dialogs[0], "currency-usd").trailing is None


async def test_currency_change_rerenders_calculate_amounts(monkeypatch):
    """Currency pick on the calculate screen rebuilds the result table in the
    new currency, keeping the computed result (not a cleared form)."""
    _use_storage(monkeypatch, FakeStorage())
    page = FakePage()
    await main(page)
    _find_by_key(page.controls[0], "menu-calculate").on_click(None)
    root = page.controls[0]
    _find_by_key(root, "estate-gross").value = "6000000"
    _find_first(root, ft.RadioGroup).value = "husband"
    _find_by_key(root, "btn-calculate").on_click(None)
    assert _find_by_key(root, "result-table") is not None
    assert "$" in _result_text(root)
    await _pick_currency(page, "idr")
    root = page.controls[0]
    assert _find_by_key(root, "result-table") is not None
    amounts = _result_text(root)
    assert "$" not in amounts
    assert "Rp" in amounts
