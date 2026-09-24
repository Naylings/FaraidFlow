import flet as ft

from app.components.language_button import LanguageButton
from app.localization.localization import Localization
from fakes import FakePage, FakeStorage


async def _loc(language="en"):
    storage = FakeStorage()
    if language != "en":
        await storage.set(Localization.STORAGE_KEY, language)
    return await Localization.load(storage, default_language="en")


async def test_button_shows_current_language():
    loc = await _loc("en")
    btn = LanguageButton(page=FakePage(), localization=loc, on_change=lambda: None)
    assert btn.button.key == "lang-button"
    assert btn.button.content == "🇬🇧 EN"


async def test_button_label_tracks_language():
    loc = await _loc("en")
    btn = LanguageButton(page=FakePage(), localization=loc, on_change=lambda: None)
    await btn.choose("id")
    new_btn = LanguageButton(page=FakePage(), localization=loc, on_change=lambda: None)
    assert new_btn.button.content == "🇮🇩 ID"


async def test_open_shows_picker_dialog():
    loc = await _loc("en")
    page = FakePage()
    btn = LanguageButton(page=page, localization=loc, on_change=lambda: None)
    btn.open()
    assert len(page.dialogs) == 1
    dialog = page.dialogs[0]
    assert isinstance(dialog, ft.AlertDialog)
    tiles = dialog.content.controls
    assert len(tiles) == 2
    assert tiles[0].title.value == "🇬🇧 English"
    assert tiles[1].title.value == "🇮🇩 Bahasa Indonesia"


async def test_choose_persists_switches_and_notifies():
    loc = await _loc("en")
    page = FakePage()
    calls = []
    btn = LanguageButton(page=page, localization=loc, on_change=lambda: calls.append("changed"))
    await btn.choose("id")
    assert loc.language == "id"
    assert calls == ["changed"]
    assert (await loc.storage.get(Localization.STORAGE_KEY)) == "id"