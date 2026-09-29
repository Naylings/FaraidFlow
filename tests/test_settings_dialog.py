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


def _tab_bar(dialog):
    # Flet 1.0 splits ft.Tabs into a column holding the headers (ft.TabBar)
    # and the pages (ft.TabBarView), so the tabs are one level deeper than the
    # dialog's content.
    return dialog.content.content.controls[0]


def _tiles(dialog, index):
    """ListTiles of the page at `index`: 0 language, 1 currency, 2 theme."""
    return dialog.content.content.controls[1].controls[index].controls


def _tile(dialog, index, key):
    return next(tile for tile in _tiles(dialog, index) if tile.key == key)


def test_settings_button_creates_tabs():
    page = FakePage()
    btn = SettingsButton(page, Localization("en", None), lambda: None)
    btn.open()
    assert len(page.dialogs) == 1
    dialog = page.dialogs[0]
    assert dialog is not None
    assert isinstance(dialog, ft.AlertDialog)
    # dialog content should be ft.Tabs with 3 tabs
    assert isinstance(dialog.content, ft.Tabs)
    assert dialog.content.length == 3
    tabs = _tab_bar(dialog).tabs
    assert len(tabs) == 3
    assert [t.label for t in tabs] == ["Language", "Currency", "Theme"]


def test_dialog_title_is_localized():
    btn = SettingsButton(FakePage(), Localization("en", None), lambda: None)
    assert _open(btn).title.value == "Settings"


async def test_every_option_is_listed():
    btn = SettingsButton(FakePage(), await _loc(), lambda: None)
    dialog = _open(btn)
    assert [t.title.value for t in _tiles(dialog, 0)] == [
        "🇬🇧 English",
        "🇮🇩 Bahasa Indonesia",
    ]
    assert [t.title.value for t in _tiles(dialog, 1)] == [
        "US Dollar (USD)",
        "Indonesian Rupiah (IDR)",
        "Malaysian Ringgit (MYR)",
        "Euro (EUR)",
        "Singapore Dollar (SGD)",
    ]
    assert [t.title.value for t in _tiles(dialog, 2)] == ["Light", "Dark", "System"]


async def test_choosing_a_language_persists_closes_and_notifies():
    loc = await _loc()
    page = FakePage()
    calls = []
    btn = SettingsButton(page, loc, on_change=lambda: calls.append("changed"))
    dialog = _open(btn)
    await _tile(dialog, 0, "lang-id").on_click(None)
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
    await _tile(dialog, 1, "currency-eur").on_click(None)
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
    await _tile(dialog, 2, "theme-dark").on_click(None)
    assert loc.theme == "dark"
    assert (await loc.storage.get(STORAGE_KEYS["theme"])) == "dark"
    assert calls == ["changed"]
    assert page.dialogs == []


async def test_current_value_is_the_only_checked_one():
    btn = SettingsButton(FakePage(), await _loc("id", "IDR", "dark"), lambda: None)
    dialog = _open(btn)
    for index, key in ((0, "lang-id"), (1, "currency-idr"), (2, "theme-dark")):
        checked = [t.key for t in _tiles(dialog, index) if t.trailing is not None]
        assert checked == [key]


async def test_options_follow_the_current_language():
    btn = SettingsButton(FakePage(), await _loc("id"), lambda: None)
    dialog = _open(btn)
    assert [t.label for t in _tab_bar(dialog).tabs] == ["Bahasa", "Mata Uang", "Tema"]
    assert [t.title.value for t in _tiles(dialog, 1)][:2] == [
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


async def test_appbar_button_shows_the_language_flag():
    page = FakePage()
    loc = await _loc()
    btn = SettingsButton(page, loc, on_change=lambda: None)
    assert btn.button.content == "🇬🇧 EN"
    await btn.choose_language("id")
    assert SettingsButton(page, loc, lambda: None).button.content == "🇮🇩 ID"


async def test_on_change_is_optional():
    loc = await _loc()
    page = FakePage()
    dialog = _open(SettingsButton(page, loc, on_change=None))
    await _tile(dialog, 0, "lang-id").on_click(None)
    assert loc.language == "id"
    assert page.dialogs == []
