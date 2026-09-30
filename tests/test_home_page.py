import flet as ft

from app.localization.localization import Localization
from app.pages.home import HomePage
from fakes import FakePage, FakeStorage


async def _home(language="en", version="0.1.0-beta.1"):
    storage = FakeStorage()
    if language != "en":
        await storage.set(Localization.STORAGE_KEY, language)
    loc = await Localization.load(storage, default_language="en")
    page = FakePage()
    home = HomePage(page, loc, version=version)
    return home, page


def _buttons(home):
    return [c for c in home.build_body().controls if isinstance(c, ft.FilledButton)]


async def test_version_line_comes_from_the_version_it_was_given():
    """The home line used to hardcode "v0.1", a second version source that
    disagreed with pyproject.toml and with the About page."""
    home, _ = await _home(version="9.9.9")
    version_line = next(c for c in home.build_body().controls if getattr(c, "key", None) == "home-version")
    assert version_line.value == "v9.9.9"
    assert version_line.size == 12, "the version line keeps its own quiet styling"


def _language_tile(dialog, code):
    """The language list tile inside the settings dialog's detail area."""
    detail = next(c for c in dialog.content.controls if getattr(c, "key", None) == "settings-detail")
    return next(t for t in detail.content.controls if t.key == f"lang-{code}")


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
    assert appbar.actions[0].key == "settings-button"
    assert appbar.actions[0].icon == ft.Icons.SETTINGS


async def test_tapping_calculate_routes_to_calculator():
    pages = []
    home, page = await _home()
    home.on_calculate = lambda: pages.append("calc")
    calculate = next(b for b in _buttons(home) if b.key == "menu-calculate")
    calculate.on_click(None)
    assert pages == ["calc"]


async def test_information_and_about_buttons_route_to_their_pages():
    """Both screens exist now, so neither menu button falls back to a snackbar."""
    calls = []
    home, page = await _home()
    home.on_information = lambda: calls.append("info")
    home.on_about = lambda: calls.append("about")
    next(b for b in _buttons(home) if b.key == "menu-information").on_click(None)
    next(b for b in _buttons(home) if b.key == "menu-about").on_click(None)
    assert calls == ["info", "about"]
    assert page.dialogs == []


async def test_a_menu_button_without_a_callback_does_nothing():
    home, page = await _home()
    next(b for b in _buttons(home) if b.key == "menu-about").on_click(None)
    assert page.dialogs == []


async def test_refresh_rebuilds_in_indonesian():
    home, page = await _home("en")
    await home.localization.set_language("id")
    home.refresh()
    assert [b.content for b in _buttons(home)] == ["Hitung", "Informasi", "Tentang"]
    assert page.appbar.title.value == "FaraidFlow"
    assert page.appbar.actions[0].icon == ft.Icons.SETTINGS


async def test_appbar_injected_on_change_replaces_refresh():
    home, page = await _home()
    calls = []
    appbar = home.build_appbar(on_change=lambda: calls.append("changed"))
    assert appbar.actions[0].key == "settings-button"
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
    assert keys == ["settings-button", "appbar-calculate"], keys
    assert page.appbar.actions[0].key == "settings-button"


async def test_refresh_without_extra_actions_adds_none():
    home, page = await _home()
    home.build_appbar()
    home.refresh()
    assert [getattr(a, "key", None) for a in page.appbar.actions] == ["settings-button"]
