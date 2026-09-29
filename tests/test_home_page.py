import flet as ft

from app.localization.localization import Localization
from app.pages.home import HomePage
from fakes import FakePage, FakeStorage


async def _home(language="en"):
    storage = FakeStorage()
    if language != "en":
        await storage.set(Localization.STORAGE_KEY, language)
    loc = await Localization.load(storage, default_language="en")
    page = FakePage()
    home = HomePage(page, loc)
    return home, page


def _buttons(home):
    return [c for c in home.build_body().controls if isinstance(c, ft.FilledButton)]


def _language_tile(dialog, code):
    """The language list tile inside the settings dialog's first tab page."""
    pages = dialog.content.content.controls[1]
    return next(t for t in pages.controls[0].controls if t.key == f"lang-{code}")


async def test_english_default_labels():
    home, _ = await _home()
    assert [b.content for b in _buttons(home)] == ["Calculate", "Information", "About"]


async def test_buttons_have_stable_keys():
    home, _ = await _home()
    assert [b.key for b in _buttons(home)] == [
        "menu-calculate",
        "menu-information",
        "menu-about",
    ]


async def test_appbar_title_and_settings_button():
    home, _ = await _home()
    appbar = home.build_appbar()
    assert appbar.title.value == "FaraidFlow"
    assert appbar.actions[0].key == "lang-button"
    assert appbar.actions[0].content == "🇬🇧 EN"


async def test_tapping_calculate_routes_to_calculator():
    pages = []
    home, page = await _home()
    home.on_calculate = lambda: pages.append("calc")
    calculate = next(b for b in _buttons(home) if b.key == "menu-calculate")
    calculate.on_click(None)
    assert pages == ["calc"]


async def test_information_and_about_still_snackbar():
    home, page = await _home()
    info = next(b for b in _buttons(home) if b.key == "menu-information")
    about = next(b for b in _buttons(home) if b.key == "menu-about")
    info.on_click(None)
    about.on_click(None)
    assert len(page.dialogs) == 2


async def test_refresh_rebuilds_in_indonesian():
    home, page = await _home("en")
    await home.localization.set_language("id")
    home.refresh()
    assert [b.content for b in _buttons(home)] == ["Hitung", "Informasi", "Tentang"]
    assert page.appbar.title.value == "FaraidFlow"
    assert page.appbar.actions[0].content == "🇮🇩 ID"


async def test_appbar_injected_on_change_replaces_refresh():
    home, page = await _home()
    calls = []
    appbar = home.build_appbar(on_change=lambda: calls.append("changed"))
    assert appbar.actions[0].key == "lang-button"
    page.appbar = appbar
    page.appbar.actions[0].on_click(None)
    await _language_tile(page.dialogs[0], "id").on_click(None)
    assert calls == ["changed"]


async def test_refresh_preserves_extra_appbar_actions():
    """refresh() is the default on_change, so it must not drop extra_actions.

    Before this was fixed, refresh() called build_appbar() with no arguments and
    silently discarded the Calculate action.
    """
    home, page = await _home()
    home.build_appbar(extra_actions=[ft.IconButton(key="appbar-calculate")])
    home.refresh()
    keys = [getattr(a, "key", None) for a in page.appbar.actions]
    assert keys == ["lang-button", "appbar-calculate"], keys
    assert page.appbar.actions[0].key == "lang-button"


async def test_refresh_without_extra_actions_adds_none():
    home, page = await _home()
    home.build_appbar()
    home.refresh()
    assert [getattr(a, "key", None) for a in page.appbar.actions] == ["lang-button"]
