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


async def test_appbar_title_and_language_button():
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