import flet as ft

from app.localization import en, id as id_table
from app.localization.localization import Localization
from app.pages.home import HomePage
from app.pages.information import InformationPage
from fakes import FakePage, FakeStorage
from main import main

# Every info.* key in the tables has to reach the page, so the expectations are
# derived from the tables rather than duplicated here (duplicating them would let
# a new key ship unrendered without a test noticing).
INFO_KEYS = sorted(k for k in en.TRANSLATIONS if k.startswith("info."))
SECTION_TITLES = ["info.intro.title", "info.legal_basis.title", "info.how_it_works.title", "info.glossary.title", "info.disclaimer.title"]


async def _info(language="en", back_home=None):
    storage = FakeStorage()
    if language != "en":
        await storage.set(Localization.STORAGE_KEY, language)
    loc = await Localization.load(storage, default_language="en")
    info = InformationPage(FakePage(), loc, back_home=back_home)
    return info


def _children(control):
    items = list(getattr(control, "controls", None) or [])
    child = getattr(control, "content", None)
    if isinstance(child, ft.Control):
        items.append(child)
    return items


def _walk(control):
    yield control
    for c in _children(control):
        yield from _walk(c)


def _texts(root):
    return [c.value for c in _walk(root) if isinstance(c, ft.Text)]


def _by_key(control, key):
    if getattr(control, "key", None) == key:
        return control
    for c in _children(control):
        found = _by_key(c, key)
        if found is not None:
            return found
    return None


def test_information_page_builds():
    p = InformationPage(FakePage(), Localization("en", None), lambda: None)
    root = p.build()
    assert isinstance(root, ft.SafeArea)


async def test_page_is_a_scrollable_column():
    info = await _info()
    root = info.build()
    assert isinstance(root.content, ft.Column)
    assert root.content.scroll == ft.ScrollMode.AUTO


async def test_five_section_titles_render_in_english():
    info = await _info()
    texts = _texts(info.build())
    expected = [en.TRANSLATIONS[k] for k in SECTION_TITLES]
    assert expected == ["Introduction", "Legal Basis", "How It Works", "Glossary", "Disclaimer"]
    for title in ("Information", *expected):
        assert title in texts, title


async def test_header_and_section_titles_are_bold_headings():
    info = await _info()
    headings = [c for c in _walk(info.build()) if isinstance(c, ft.Text) and c.weight == ft.FontWeight.BOLD]
    values = [h.value for h in headings]
    assert values[0] == "Information", "the header title is the first heading"
    assert values[1:] == ["Introduction", "Legal Basis", "How It Works", "Glossary", "Disclaimer"]
    assert headings[0].size == 22, "the header title keeps the calculator's title size"
    assert {h.size for h in headings[1:]} == {20}


async def test_every_info_key_is_rendered_in_english():
    info = await _info()
    texts = _texts(info.build())
    missing = [k for k in INFO_KEYS if en.TRANSLATIONS[k] not in texts]
    assert missing == []


async def test_every_info_key_is_rendered_in_indonesian():
    info = await _info("id")
    texts = _texts(info.build())
    missing = [k for k in INFO_KEYS if id_table.TRANSLATIONS[k] not in texts]
    assert missing == []


async def test_switching_language_rebuilds_the_page_in_indonesian():
    info = await _info()
    assert "Introduction" in _texts(info.build())
    await info.loc.set_language("id")
    texts = _texts(info.build())
    assert [t for t in texts if t in ("Pengantar", "Dasar Hukum", "Cara Kerja", "Istilah", "Penafian")] == [
        "Pengantar",
        "Dasar Hukum",
        "Cara Kerja",
        "Istilah",
        "Penafian",
    ]
    assert "Introduction" not in texts


async def test_glossary_entries_are_whole_lines():
    """Each glossary value is a whole 'Term - definition' line, so it must not
    be split into separate controls (or the term and definition could drift)."""
    info = await _info()
    texts = _texts(info.build())
    for key in INFO_KEYS:
        if key.startswith("info.glossary.") and key != "info.glossary.title":
            assert texts.count(en.TRANSLATIONS[key]) == 1, key


async def test_back_button_invokes_back_home():
    calls = []
    info = await _info(back_home=lambda: calls.append("home"))
    back = _by_key(info.build(), "back-home")
    assert isinstance(back, ft.IconButton)
    assert back.tooltip == en.TRANSLATIONS["calc.back"]
    back.on_click(None)
    assert calls == ["home"]


async def test_back_button_is_a_noop_without_a_callback():
    info = await _info(back_home=None)
    _by_key(info.build(), "back-home").on_click(None)


async def test_home_information_button_routes_to_the_page():
    calls = []
    page = FakePage()
    home = HomePage(page, await Localization.load(FakeStorage()), on_information=lambda: calls.append("info"))
    _by_key(home.build(), "menu-information").on_click(None)
    assert calls == ["info"]
    assert page.dialogs == [], "Information is no longer a 'coming soon' screen"


async def test_home_about_button_routes_to_the_page():
    calls = []
    page = FakePage()
    home = HomePage(page, await Localization.load(FakeStorage()), on_about=lambda: calls.append("about"))
    _by_key(home.build(), "menu-about").on_click(None)
    assert calls == ["about"]
    assert page.dialogs == [], "About is no longer a 'coming soon' screen"


async def test_main_routes_home_information_and_back():
    page = FakePage()
    await main(page)
    _by_key(page.controls[0], "menu-information").on_click(None)
    root = page.controls[0]
    assert isinstance(root, ft.SafeArea)
    assert "Introduction" in _texts(root)
    _by_key(root, "back-home").on_click(None)
    assert _by_key(page.controls[0], "menu-calculate") is not None


async def test_main_language_switch_keeps_the_information_page():
    page = FakePage()
    await main(page)
    _by_key(page.controls[0], "menu-information").on_click(None)
    page.appbar.actions[0].on_click(None)
    id_tile = _by_key(page.dialogs[0], "lang-id")
    await id_tile.on_click(None)
    root = page.controls[0]
    texts = _texts(root)
    assert "Pengantar" in texts
    assert "Introduction" not in texts
    assert page.appbar.actions[0].content == "\U0001F1EE\U0001F1E9 ID", "the appbar must be rebuilt with the new language"
    _by_key(root, "back-home").on_click(None)
    assert _by_key(page.controls[0], "menu-calculate").content == "Hitung"
