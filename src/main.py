from pathlib import Path

import flet as ft
import tomllib

from app.localization.localization import THEMES, Localization
from app.pages.about import APP_NAME, AboutPage
from app.pages.calculate import CalculationPage, is_two_pane
from app.pages.home import HomePage
from app.pages.information import InformationPage

# The THEMES codes (light/dark/system) are the ft.ThemeMode member names, lowercased.
THEME_MODES = {theme["code"]: ft.ThemeMode[theme["code"].upper()] for theme in THEMES}

# Resolved from this file, never the working directory: a packaged app starts
# wherever it was launched from, and main.py sits one level under the project
# root. A build also has no pyproject.toml next to the source at all, so every
# failure below is expected rather than exceptional.
PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
FALLBACK_VERSION = "unknown"


def read_version(pyproject: Path | None = None) -> str:
    """The version to show on the About page, or FALLBACK_VERSION.

    A missing file, an unreadable one, a [project] table with no version, and a
    parse error all land on the same answer: a wrong version on screen is worse
    than admitting the app does not know, and neither may stop it from starting.
    """
    path = pyproject or PYPROJECT
    try:
        with path.open("rb") as handle:
            project = tomllib.load(handle).get("project", {})
        version = project.get("version") if isinstance(project, dict) else None
    except (OSError, ValueError):  # TOMLDecodeError and UnicodeDecodeError are both ValueErrors
        return FALLBACK_VERSION
    return version if isinstance(version, str) and version else FALLBACK_VERSION


def apply_theme(page: ft.Page, localization: Localization) -> None:
    """Put the stored theme on the page; an unknown code falls back to system."""
    page.theme_mode = THEME_MODES.get(localization.theme, ft.ThemeMode.SYSTEM)


async def main(page: ft.Page):
    page.title = APP_NAME
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN)

    prefs = ft.SharedPreferences()
    localization = await Localization.load(prefs, default_language="en")
    apply_theme(page, localization)

    home = HomePage(page, localization)
    version = read_version()
    screen = {"name": "home"}
    calc = None
    info = None
    about = None

    def show_content(control):
        page.clean()
        page.add(control)
        page.update()

    def build_appbar():
        extra = None
        if screen["name"] == "calc" and calc is not None:
            extra = [calc.build_appbar_action()]
        return home.build_appbar(on_change=on_settings_changed, extra_actions=extra)

    def on_settings_changed():
        # Fires for every settings pick - language, currency or theme.
        apply_theme(page, localization)
        if screen["name"] == "calc" and calc is not None:
            refresh_calculate()
        elif screen["name"] == "information" and info is not None:
            refresh_information()
        elif screen["name"] == "about" and about is not None:
            refresh_about()
        else:
            show_home()

    def show_home():
        # The other screens hold nothing worth carrying back, so they are
        # dropped together; the next visit builds a fresh one.
        nonlocal calc, info, about
        screen["name"] = "home"
        calc = None
        info = None
        about = None
        page.appbar = build_appbar()
        home.body = home.build_body()
        show_content(home.build())
        page.update()

    def show_calculate():
        nonlocal calc
        calc = CalculationPage(page, localization, back_home=show_home)
        screen["name"] = "calc"
        refresh_calculate()

    def refresh_calculate():
        state = calc.capture_state()
        page.appbar = build_appbar()
        root = calc.build()
        calc.restore_state(state)
        show_content(root)
        page.update()

    def show_information():
        nonlocal info
        info = InformationPage(page, localization, back_home=show_home)
        screen["name"] = "information"
        refresh_information()

    def refresh_information():
        # The page holds no state, so a rebuild is the whole refresh; the appbar
        # goes with it so the settings button shows the new language.
        page.appbar = build_appbar()
        show_content(info.build())
        page.update()

    def show_about():
        nonlocal about
        about = AboutPage(page, localization, back_home=show_home, version=version)
        screen["name"] = "about"
        refresh_about()

    def refresh_about():
        page.appbar = build_appbar()
        show_content(about.build())
        page.update()

    def on_page_resize(e):
        if (
            screen["name"] == "calc"
            and calc is not None
            and calc.two_pane != is_two_pane(getattr(page, "width", None))
        ):
            refresh_calculate()

    page.on_resize = on_page_resize

    home.on_calculate = show_calculate
    home.on_information = show_information
    home.on_about = show_about
    screen["name"] = "home"
    page.appbar = build_appbar()
    page.add(home.build())
    page.update()


if __name__ == "__main__":
    ft.run(main)