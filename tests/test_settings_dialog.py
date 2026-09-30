import flet as ft
from fakes import FakePage, FakeStorage

from app.components.settings_button import SettingsButton
from app.localization.localization import STORAGE_KEYS, Localization


async def _loc(language="en", currency="USD", theme="system"):
    storage = FakeStorage()
    if language != "en":
        await storage.set(Localization.STORAGE_KEY, language)
    if currency != "USD":
        await storage.set(STORAGE_KEYS["currency"], currency)
    if theme != "system":
        await storage.set(STORAGE_KEYS["theme"], theme)
    return await Localization.load(storage, default_language="en")


def _open(settings_button):
    """Open the dialog on the button's page and hand the dialog back."""
    settings_button.open()
    dialogs = settings_button.page.dialogs
    assert len(dialogs) == 1, f"expected exactly one dialog, got {len(dialogs)}"
    return dialogs[0]


def _children(control):
    items = list(getattr(control, "controls", None) or [])
    content = getattr(control, "content", None)
    if content is not None and isinstance(content, ft.Control):
        items.append(content)
    return items


def _find_by_key(control, key):
    if getattr(control, "key", None) == key:
        return control
    for c in _children(control):
        found = _find_by_key(c, key)
        if found is not None:
            return found
    return None


def _detail_tiles(dialog):
    """Option ListTiles of the currently selected category page."""
    return _find_by_key(dialog, "settings-detail").content.controls


def _tile(dialog, key):
    tile = _find_by_key(dialog, key)
    assert tile is not None, f"expected a tile with key {key!r}"
    return tile


async def test_settings_dialog_opens_on_language():
    page = FakePage()
    loc = Localization("en", None)
    btn = SettingsButton(page, loc, on_change=lambda: None)
    btn.open()
    assert len(page.dialogs) == 1
    dialog = page.dialogs[0]
    assert isinstance(dialog, ft.AlertDialog)
    cats = [_find_by_key(dialog, k) for k in ("cat-language", "cat-currency", "cat-theme")]
    assert [c.title.value for c in cats] == ["Language", "Currency", "Theme"]
    assert cats[0].trailing is not None
    assert cats[1].trailing is None and cats[2].trailing is None
    detail = _find_by_key(dialog, "settings-detail")
    assert [c.key for c in detail.content.controls] == ["lang-en", "lang-id"]


async def test_tapping_currency_category_shows_currency_options():
    page = FakePage()
    loc = Localization("en", None)
    btn = SettingsButton(page, loc, on_change=lambda: None)
    btn.open()
    dialog = page.dialogs[0]
    await _find_by_key(dialog, "cat-currency").on_click(None)
    assert _find_by_key(dialog, "cat-currency").trailing is not None
    assert _find_by_key(dialog, "cat-language").trailing is None
    detail = _find_by_key(dialog, "settings-detail")
    assert [c.key for c in detail.content.controls] == [
        "currency-usd", "currency-idr", "currency-myr", "currency-eur", "currency-sgd",
    ]


async def test_choosing_currency_persists_closes_and_notifies():
    storage = FakeStorage()
    loc = await Localization.load(storage, default_language="en")
    page = FakePage()
    calls = []
    btn = SettingsButton(page, loc, on_change=lambda: calls.append("changed"))
    btn.open()
    dialog = page.dialogs[0]
    await _find_by_key(dialog, "cat-currency").on_click(None)
    await _find_by_key(dialog, "currency-idr").on_click(None)
    assert loc.currency == "IDR"
    assert await storage.get("faraidflow.currency") == "IDR"
    assert page.dialogs == []
    assert calls == ["changed"]


def test_settings_button_creates_stacked_categories():
    page = FakePage()
    btn = SettingsButton(page, Localization("en", None), lambda: None)
    btn.open()
    assert len(page.dialogs) == 1
    dialog = page.dialogs[0]
    assert dialog is not None
    assert isinstance(dialog, ft.AlertDialog)
    # dialog content is a column: category master row on top, detail list below
    assert isinstance(dialog.content, ft.Column)
    cats = [_find_by_key(dialog, k) for k in ("cat-language", "cat-currency", "cat-theme")]
    assert len(cats) == 3
    assert [t.title.value for t in cats] == ["Language", "Currency", "Theme"]
    assert _find_by_key(dialog, "settings-detail") is not None


def test_dialog_title_is_localized():
    btn = SettingsButton(FakePage(), Localization("en", None), lambda: None)
    assert _open(btn).title.value == "Settings"


async def test_every_option_is_listed():
    btn = SettingsButton(FakePage(), await _loc(), lambda: None)
    dialog = _open(btn)
    assert [t.title.value for t in _detail_tiles(dialog)] == [
        "🇬🇧 English",
        "🇮🇩 Bahasa Indonesia",
    ]
    await _find_by_key(dialog, "cat-currency").on_click(None)
    assert [t.title.value for t in _detail_tiles(dialog)] == [
        "US Dollar (USD)",
        "Indonesian Rupiah (IDR)",
        "Malaysian Ringgit (MYR)",
        "Euro (EUR)",
        "Singapore Dollar (SGD)",
    ]
    await _find_by_key(dialog, "cat-theme").on_click(None)
    assert [t.title.value for t in _detail_tiles(dialog)] == ["Light", "Dark", "System"]


async def test_choosing_a_language_persists_closes_and_notifies():
    loc = await _loc()
    page = FakePage()
    calls = []
    btn = SettingsButton(page, loc, on_change=lambda: calls.append("changed"))
    dialog = _open(btn)
    await _tile(dialog, "lang-id").on_click(None)
    assert loc.language == "id"
    assert (await loc.storage.get(Localization.STORAGE_KEY)) == "id"
    assert calls == ["changed"]
    assert page.dialogs == []


async def test_choosing_a_currency_persists_closes_and_notifies():
    loc = await _loc()
    page = FakePage()
    calls = []
    btn = SettingsButton(page, loc, on_change=lambda: calls.append("changed"))
    dialog = _open(btn)
    await _tile(dialog, "cat-currency").on_click(None)
    await _tile(dialog, "currency-eur").on_click(None)
    assert loc.currency == "EUR"
    assert (await loc.storage.get(STORAGE_KEYS["currency"])) == "EUR"
    assert calls == ["changed"]
    assert page.dialogs == []


async def test_choosing_a_theme_persists_closes_and_notifies():
    loc = await _loc()
    page = FakePage()
    calls = []
    btn = SettingsButton(page, loc, on_change=lambda: calls.append("changed"))
    dialog = _open(btn)
    await _tile(dialog, "cat-theme").on_click(None)
    await _tile(dialog, "theme-dark").on_click(None)
    assert loc.theme == "dark"
    assert (await loc.storage.get(STORAGE_KEYS["theme"])) == "dark"
    assert calls == ["changed"]
    assert page.dialogs == []


async def test_current_value_is_the_only_checked_one():
    btn = SettingsButton(FakePage(), await _loc("id", "IDR", "dark"), lambda: None)
    dialog = _open(btn)
    for cat, key in (("cat-language", "lang-id"), ("cat-currency", "currency-idr"), ("cat-theme", "theme-dark")):
        await _tile(dialog, cat).on_click(None)
        checked = [t.key for t in _detail_tiles(dialog) if t.trailing is not None]
        assert checked == [key]


async def test_options_follow_the_current_language():
    btn = SettingsButton(FakePage(), await _loc("id"), lambda: None)
    dialog = _open(btn)
    assert [_find_by_key(dialog, k).title.value for k in ("cat-language", "cat-currency", "cat-theme")] == ["Bahasa", "Mata Uang", "Tema"]
    await _tile(dialog, "cat-currency").on_click(None)
    assert [t.title.value for t in _detail_tiles(dialog)][:2] == [
        "Dolar AS (USD)",
        "Rupiah Indonesia (IDR)",
    ]


async def test_appbar_button_is_the_settings_button():
    """It opens all three settings, so it is keyed and tooltipped as settings."""
    btn = SettingsButton(FakePage(), await _loc(), on_change=lambda: None)
    assert btn.button.key == "settings-button"
    assert btn.button.tooltip == "Settings"
    id_btn = SettingsButton(FakePage(), await _loc("id"), on_change=lambda: None)
    assert id_btn.button.tooltip == "Pengaturan"


async def test_appbar_button_shows_the_settings_icon():
    page = FakePage()
    loc = await _loc()
    btn = SettingsButton(page, loc, on_change=lambda: None)
    assert btn.button.icon == ft.Icons.SETTINGS
    await btn.choose_language("id")
    assert SettingsButton(page, loc, lambda: None).button.icon == ft.Icons.SETTINGS


async def test_on_change_is_optional():
    loc = await _loc()
    page = FakePage()
    dialog = _open(SettingsButton(page, loc, on_change=None))
    await _tile(dialog, "lang-id").on_click(None)
    assert loc.language == "id"
    assert page.dialogs == []
