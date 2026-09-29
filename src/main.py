import flet as ft

from app.localization.localization import THEMES, Localization
from app.pages.calculate import CalculationPage, is_two_pane
from app.pages.home import HomePage
from app.pages.information import InformationPage

# The THEMES codes (light/dark/system) are the ft.ThemeMode member names, lowercased.
THEME_MODES = {theme["code"]: ft.ThemeMode[theme["code"].upper()] for theme in THEMES}


def apply_theme(page: ft.Page, localization: Localization) -> None:
    """Put the stored theme on the page; an unknown code falls back to system."""
    page.theme_mode = THEME_MODES.get(localization.theme, ft.ThemeMode.SYSTEM)


async def main(page: ft.Page):
    page.title = "FaraidFlow"
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN)

    prefs = ft.SharedPreferences()
    localization = await Localization.load(prefs, default_language="en")
    apply_theme(page, localization)

    home = HomePage(page, localization)
    screen = {"name": "home"}
    calc = None
    info = None

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
        else:
            show_home()

    def show_home():
        nonlocal calc
        screen["name"] = "home"
        calc = None
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
    screen["name"] = "home"
    page.appbar = build_appbar()
    page.add(home.build())
    page.update()


if __name__ == "__main__":
    ft.run(main)