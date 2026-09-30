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


def _choice_tiles(choice):
    """Option ListTiles of an open per-setting choice dialog."""
    return choice.content.controls


def _tile(dialog, key):
    tile = _find_by_key(dialog, key)
    assert tile is not None, f"expected a tile with key {key!r}"
    return tile


async def _open_choice(btn, code):
    """Tap a summary value button and hand back the new choice dialog."""
    page = btn.page
    before = len(page.dialogs)
    await _find_by_key(page.dialogs[0], f"setting-value-{code}").on_click(None)
    assert len(page.dialogs) == before + 1
    return page.dialogs[-1]


def _summary_values(dialog):
    rows = dialog.content.controls
    return [r.controls[1].content for r in rows]


async def test_settings_dialog_shows_summary_values():
    page = FakePage()
    loc = Localization("en", None)
    btn = SettingsButton(page, loc, on_change=lambda: None)
    btn.open()
    assert len(page.dialogs) == 1
    dialog = page.dialogs[0]
    assert isinstance(dialog, ft.AlertDialog)
    rows = dialog.content.controls
    assert [r.controls[0].value for r in rows] == ["Language", "Currency", "Theme"]
    assert [r.controls[1].key for r in rows] == [
        "setting-value-language", "setting-value-currency", "setting-value-theme",
    ]
    assert [r.controls[1].content for r in rows] == ["🇬🇧 English", "US Dollar (USD)", "System"]


async def test_tapping_currency_value_shows_currency_options():
    page = FakePage()
    loc = Localization("en", None)
    btn = SettingsButton(page, loc, on_change=lambda: None)
    btn.open()
    choice = await _open_choice(btn, "currency")
    assert isinstance(choice, ft.AlertDialog)
    assert choice.title.value == "Currency"
    assert [c.key for c in choice.content.controls] == [
        "currency-usd", "currency-idr", "currency-myr", "currency-eur", "currency-sgd",
    ]
    # the summary underneath stays open
    assert len(page.dialogs) == 2


async def test_choosing_currency_persists_returns_and_notifies():
    storage = FakeStorage()
    loc = await Localization.load(storage, default_language="en")
    page = FakePage()
    calls = []
    btn = SettingsButton(page, loc, on_change=lambda: calls.append("changed"))
    btn.open()
    await _find_by_key(page.dialogs[0], "setting-value-currency").on_click(None)
    await _find_by_key(page.dialogs[1], "currency-idr").on_click(None)
    assert loc.currency == "IDR"
    assert await storage.get("faraidflow.currency") == "IDR"
    assert len(page.dialogs) == 1
    assert _find_by_key(page.dialogs[0], "setting-value-currency").content == "Indonesian Rupiah (IDR)"
    assert calls == ["changed"]


def test_settings_button_creates_summary_rows():
    page = FakePage()
    btn = SettingsButton(page, Localization("en", None), lambda: None)
    btn.open()
    assert len(page.dialogs) == 1
    dialog = page.dialogs[0]
    assert dialog is not None
    assert isinstance(dialog, ft.AlertDialog)
    # dialog content is a column of summary rows: name label + value button
    assert isinstance(dialog.content, ft.Column)
    rows = dialog.content.controls
    assert len(rows) == 3
    assert [r.controls[0].value for r in rows] == ["Language", "Currency", "Theme"]
    assert [r.controls[1].key for r in rows] == [
        "setting-value-language", "setting-value-currency", "setting-value-theme",
    ]


def test_dialog_title_is_localized():
    btn = SettingsButton(FakePage(), Localization("en", None), lambda: None)
    assert _open(btn).title.value == "Settings"


async def test_every_option_is_listed():
    btn = SettingsButton(FakePage(), await _loc(), lambda: None)
    dialog = _open(btn)
    assert [t.title.value for t in _choice_tiles(await _open_choice(btn, "language"))] == [
        "🇬🇧 English",
        "🇮🇩 Bahasa Indonesia",
    ]
    btn.page.pop_dialog()
    assert [t.title.value for t in _choice_tiles(await _open_choice(btn, "currency"))] == [
        "US Dollar (USD)",
        "Indonesian Rupiah (IDR)",
        "Malaysian Ringgit (MYR)",
        "Euro (EUR)",
        "Singapore Dollar (SGD)",
    ]
    btn.page.pop_dialog()
    assert [t.title.value for t in _choice_tiles(await _open_choice(btn, "theme"))] == ["Light", "Dark", "System"]


async def test_choosing_a_language_persists_returns_and_notifies():
    loc = await _loc()
    page = FakePage()
    calls = []
    btn = SettingsButton(page, loc, on_change=lambda: calls.append("changed"))
    dialog = _open(btn)
    await _tile(dialog, "setting-value-language").on_click(None)
    await _tile(page.dialogs[1], "lang-id").on_click(None)
    assert loc.language == "id"
    assert (await loc.storage.get(Localization.STORAGE_KEY)) == "id"
    assert calls == ["changed"]
    assert len(page.dialogs) == 1
    assert _summary_values(page.dialogs[0])[0] == "🇮🇩 Bahasa Indonesia"


async def test_choosing_a_currency_persists_returns_and_notifies():
    loc = await _loc()
    page = FakePage()
    calls = []
    btn = SettingsButton(page, loc, on_change=lambda: calls.append("changed"))
    dialog = _open(btn)
    await _tile(dialog, "setting-value-currency").on_click(None)
    await _tile(page.dialogs[1], "currency-eur").on_click(None)
    assert loc.currency == "EUR"
    assert (await loc.storage.get(STORAGE_KEYS["currency"])) == "EUR"
    assert calls == ["changed"]
    assert len(page.dialogs) == 1
    assert _summary_values(page.dialogs[0])[1] == "Euro (EUR)"


async def test_choosing_a_theme_persists_returns_and_notifies():
    loc = await _loc()
    page = FakePage()
    calls = []
    btn = SettingsButton(page, loc, on_change=lambda: calls.append("changed"))
    dialog = _open(btn)
    await _tile(dialog, "setting-value-theme").on_click(None)
    await _tile(page.dialogs[1], "theme-dark").on_click(None)
    assert loc.theme == "dark"
    assert (await loc.storage.get(STORAGE_KEYS["theme"])) == "dark"
    assert calls == ["changed"]
    assert len(page.dialogs) == 1
    assert _summary_values(page.dialogs[0])[2] == "Dark"


async def test_current_value_is_the_only_checked_one():
    btn = SettingsButton(FakePage(), await _loc("id", "IDR", "dark"), lambda: None)
    _open(btn)
    for setting, key in (("language", "lang-id"), ("currency", "currency-idr"), ("theme", "theme-dark")):
        choice = await _open_choice(btn, setting)
        checked = [t.key for t in _choice_tiles(choice) if t.trailing is not None]
        assert checked == [key]
        btn.page.pop_dialog()


async def test_options_follow_the_current_language():
    btn = SettingsButton(FakePage(), await _loc("id"), lambda: None)
    dialog = _open(btn)
    assert [r.controls[0].value for r in dialog.content.controls] == ["Bahasa", "Mata Uang", "Tema"]
    choice = await _open_choice(btn, "currency")
    assert choice.title.value == "Mata Uang"
    assert [t.title.value for t in _choice_tiles(choice)][:2] == [
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
    btn.open()
    await btn.choose_language("id")
    assert SettingsButton(page, loc, lambda: None).button.icon == ft.Icons.SETTINGS


async def test_on_change_is_optional():
    loc = await _loc()
    page = FakePage()
    btn = SettingsButton(page, loc, on_change=None)
    dialog = _open(btn)
    await _tile(dialog, "setting-value-language").on_click(None)
    await _tile(page.dialogs[1], "lang-id").on_click(None)
    assert loc.language == "id"
    assert len(page.dialogs) == 1


async def test_settings_dialog_shows_summary_rows():
    page = FakePage()
    loc = Localization("en", None)
    btn = SettingsButton(page, loc, on_change=lambda: None)
    btn.open()
    assert len(page.dialogs) == 1
    dialog = page.dialogs[0]
    assert isinstance(dialog, ft.AlertDialog)
    rows = dialog.content.controls
    assert [r.controls[0].value for r in rows] == ["Language", "Currency", "Theme"]
    assert [r.controls[1].key for r in rows] == [
        "setting-value-language", "setting-value-currency", "setting-value-theme",
    ]
    assert [r.controls[1].content for r in rows] == ["🇬🇧 English", "US Dollar (USD)", "System"]


async def test_tapping_currency_value_opens_choice_dialog():
    page = FakePage()
    loc = Localization("en", None)
    btn = SettingsButton(page, loc, on_change=lambda: None)
    btn.open()
    await _find_by_key(page.dialogs[0], "setting-value-currency").on_click(None)
    assert len(page.dialogs) == 2
    choice = page.dialogs[1]
    assert isinstance(choice, ft.AlertDialog)
    assert choice.title.value == "Currency"
    assert [c.key for c in choice.content.controls] == [
        "currency-usd", "currency-idr", "currency-myr", "currency-eur", "currency-sgd",
    ]


async def test_choosing_currency_returns_to_updated_summary():
    storage = FakeStorage()
    loc = await Localization.load(storage, default_language="en")
    page = FakePage()
    calls = []
    btn = SettingsButton(page, loc, on_change=lambda: calls.append("changed"))
    btn.open()
    await _find_by_key(page.dialogs[0], "setting-value-currency").on_click(None)
    await _find_by_key(page.dialogs[1], "currency-idr").on_click(None)
    assert loc.currency == "IDR"
    assert await storage.get("faraidflow.currency") == "IDR"
    assert len(page.dialogs) == 1
    assert _find_by_key(page.dialogs[0], "setting-value-currency").content == "Indonesian Rupiah (IDR)"
    assert calls == ["changed"]

async def test_settings_dialogs_share_fixed_width_with_aligned_columns():
    loc = Localization("en", None)
    page = FakePage()
    btn = SettingsButton(page, loc, on_change=lambda: None)
    btn.open()
    dialog = page.dialogs[0]
    assert dialog.content.width == 320
    for row in dialog.content.controls:
        assert row.alignment == ft.MainAxisAlignment.SPACE_BETWEEN
        assert row.controls[0].text_align == ft.TextAlign.LEFT
    await _find_by_key(dialog, "setting-value-currency").on_click(None)
    assert page.dialogs[1].content.width == 320
