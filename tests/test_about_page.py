import tomllib

import flet as ft

from app.localization import en, id as id_table
from app.localization.localization import Localization
from app.pages.about import APP_NAME, AUTHOR, CREDITS, GITHUB_URL, LICENSE, LOCATION, AboutPage
from fakes import FakePage, FakeStorage
from main import FALLBACK_VERSION, PYPROJECT, main, read_version

# Every about.* key in the tables has to reach the page, so the expectation is
# derived from the tables rather than duplicated here (duplicating them would
# let a new key ship unrendered without a test noticing).
ABOUT_KEYS = sorted(k for k in en.TRANSLATIONS if k.startswith("about."))
# The rows of the spec's about table, minus the app-name row that the header
# and the identity line already carry.
SECTION_LABELS = ["about.author", "about.location", "about.credits", "about.license", "about.github"]
TEST_VERSION = "0.1.0-beta.2"


async def _about(language="en", back_home=None, version=TEST_VERSION):
    storage = FakeStorage()
    if language != "en":
        await storage.set(Localization.STORAGE_KEY, language)
    loc = await Localization.load(storage, default_language="en")
    return AboutPage(FakePage(), loc, back_home=back_home, version=version)


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


def _labels(root):
    """Every string the page shows, in tree order: text values and button labels."""
    return [
        c.value if isinstance(c, ft.Text) else c.content
        for c in _walk(root)
        if isinstance(c, (ft.Text, ft.FilledButton))
    ]


def _by_key(control, key):
    if getattr(control, "key", None) == key:
        return control
    for c in _children(control):
        found = _by_key(c, key)
        if found is not None:
            return found
    return None


def test_about_page_builds():
    p = AboutPage(FakePage(), Localization("en", None), lambda: None, version=TEST_VERSION)
    root = p.build()
    assert isinstance(root, ft.SafeArea)


async def test_page_is_a_scrollable_column():
    about = await _about()
    root = about.build()
    assert isinstance(root.content, ft.Column)
    assert root.content.scroll == ft.ScrollMode.AUTO


async def test_version_from_pyproject_reaches_the_page():
    about = await _about(version="0.1.0-beta.2")
    assert f"{APP_NAME} v0.1.0-beta.2" in _labels(about.build()), "the version passed in is the version shown"


async def test_the_seven_rows_render_in_reading_order():
    """Spec order: app+version, author, location, credits, license, github."""
    about = await _about()
    labels = _labels(about.build())
    assert labels[0] == "About", "the header title leads"
    assert labels[1] == f"{APP_NAME} v{TEST_VERSION}"
    assert labels[2::2] == [en.TRANSLATIONS[k] for k in SECTION_LABELS]
    assert labels[3::2] == [AUTHOR, LOCATION, CREDITS, LICENSE, GITHUB_URL], "each label sits above its own value"


async def test_header_and_section_titles_are_bold_headings():
    about = await _about()
    headings = [c for c in _walk(about.build()) if isinstance(c, ft.Text) and c.weight == ft.FontWeight.BOLD]
    assert [h.value for h in headings] == [
        "About",
        f"{APP_NAME} v{TEST_VERSION}",
        *[en.TRANSLATIONS[k] for k in SECTION_LABELS],
    ]
    assert headings[0].size == 22, "the header title keeps the calculator's title size"
    assert headings[1].size == 18, "the app name sits between the header and the sections"
    assert {h.size for h in headings[2:]} == {20}


async def test_license_and_github_row_values():
    about = await _about()
    labels = _labels(about.build())
    assert "MIT" in labels, "the repository ships an MIT LICENSE"
    assert GITHUB_URL in labels
    assert GITHUB_URL == "https://github.com/Naylings/FaraidFlow"


async def test_credits_name_the_software_and_the_sources():
    about = await _about()
    labels = _labels(about.build())
    credits = labels[labels.index(en.TRANSLATIONS["about.credits"]) + 1]
    for expected in ("Flet", "Flutter", "Python", "BAZNAS"):
        assert expected in credits, expected


async def test_every_about_key_is_rendered_in_english():
    about = await _about()
    labels = _labels(about.build())
    missing = [k for k in ABOUT_KEYS if k not in ("about.donate", "about.donate_soon") and en.TRANSLATIONS[k] not in labels]
    assert missing == []


async def test_every_about_key_is_rendered_in_indonesian():
    about = await _about("id")
    labels = _labels(about.build())
    missing = [k for k in ABOUT_KEYS if k not in ("about.donate", "about.donate_soon") and id_table.TRANSLATIONS[k] not in labels]
    assert missing == []


async def test_switching_language_rebuilds_the_page_in_indonesian():
    about = await _about()
    await about.loc.set_language("id")
    labels = _labels(about.build())
    assert [t for t in labels if t in {id_table.TRANSLATIONS[k] for k in SECTION_LABELS}] == [
        id_table.TRANSLATIONS[k] for k in SECTION_LABELS
    ]
    assert "Author" not in labels
    assert f"{APP_NAME} v{TEST_VERSION}" in labels, "the values are the same in both languages"


async def test_back_button_invokes_back_home():
    calls = []
    about = await _about(back_home=lambda: calls.append("home"))
    back = _by_key(about.build(), "back-home")
    assert isinstance(back, ft.IconButton)
    assert back.tooltip == en.TRANSLATIONS["calc.back"]
    back.on_click(None)
    assert calls == ["home"]


async def test_back_button_is_a_noop_without_a_callback():
    about = await _about(back_home=None)
    _by_key(about.build(), "back-home").on_click(None)


def test_read_version_reads_the_version_the_project_declares():
    declared = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]
    assert read_version() == declared


def test_read_version_honours_the_file_it_is_given(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nversion = "9.9.9"\n', encoding="utf-8")
    assert read_version(pyproject) == "9.9.9"


def test_read_version_falls_back_when_the_file_is_missing(tmp_path):
    """A packaged build has no pyproject.toml beside the source at all."""
    assert read_version(tmp_path / "pyproject.toml") == FALLBACK_VERSION


def test_the_fallback_is_the_version_pyproject_declares():
    """The fallback is what every released build shows, because `flet build`
    ships no pyproject.toml - so it is a real version, and the one the project
    declares. The two are duplicated on purpose (a bundle cannot read the file
    it was built from); this test is what keeps them in step at release time."""
    declared = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]
    assert FALLBACK_VERSION == declared
    assert FALLBACK_VERSION != "unknown", "a user-visible 'vunknown' tells them nothing"


def test_read_version_falls_back_when_the_file_cannot_be_read(tmp_path):
    unreadable = tmp_path / "pyproject.toml"
    unreadable.mkdir()
    assert read_version(unreadable) == FALLBACK_VERSION


def test_read_version_falls_back_when_the_version_key_is_missing(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "ahli-waris"\n', encoding="utf-8")
    assert read_version(pyproject) == FALLBACK_VERSION


def test_read_version_falls_back_when_the_file_is_not_valid_toml(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("project = [unclosed", encoding="utf-8")
    assert read_version(pyproject) == FALLBACK_VERSION


async def test_main_routes_home_about_and_back():
    page = FakePage()
    await main(page)
    _by_key(page.controls[0], "menu-about").on_click(None)
    root = page.controls[0]
    assert "Indonesia" in _labels(root)
    _by_key(root, "back-home").on_click(None)
    assert _by_key(page.controls[0], "menu-calculate") is not None


async def test_main_shows_the_version_declared_in_pyproject():
    page = FakePage()
    await main(page)
    _by_key(page.controls[0], "menu-about").on_click(None)
    declared = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]
    assert f"{APP_NAME} v{declared}" in _labels(page.controls[0])


async def test_home_and_about_show_the_same_version():
    """main() reads the version once and both screens render that one value, so
    the home line and the About page can never disagree."""
    page = FakePage()
    await main(page)
    home_version = _by_key(page.controls[0], "home-version")
    assert home_version is not None, "the home screen keeps its version line"
    _by_key(page.controls[0], "menu-about").on_click(None)
    assert f"{APP_NAME} {home_version.value}" in _labels(page.controls[0])
    _by_key(page.controls[0], "back-home").on_click(None)
    assert _by_key(page.controls[0], "home-version").value == home_version.value


async def test_main_language_switch_keeps_the_about_page():
    page = FakePage()
    await main(page)
    _by_key(page.controls[0], "menu-about").on_click(None)
    page.appbar.actions[0].on_click(None)
    await _by_key(page.dialogs[0], "lang-id").on_click(None)
    labels = _labels(page.controls[0])
    assert [t for t in labels if t in {id_table.TRANSLATIONS[k] for k in SECTION_LABELS}] == [
        id_table.TRANSLATIONS[k] for k in SECTION_LABELS
    ]
    assert page.appbar.actions[0].icon == ft.Icons.SETTINGS
    assert page.appbar.actions[0].tooltip == id_table.TRANSLATIONS["settings.title"], "the appbar must be rebuilt with the new language"
    _by_key(page.controls[0], "back-home").on_click(None)
    assert _by_key(page.controls[0], "menu-calculate").content == "Hitung"


async def test_main_theme_switch_keeps_the_about_page():
    page = FakePage()
    await main(page)
    _by_key(page.controls[0], "menu-about").on_click(None)
    page.appbar.actions[0].on_click(None)
    await _by_key(page.dialogs[0], "theme-dark").on_click(None)
    assert page.theme_mode is ft.ThemeMode.DARK
    assert "Author" in _labels(page.controls[0])
