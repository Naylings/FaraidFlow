import flet as ft

from app.localization.localization import Localization
from app.pages.calculate import CalculationPage
from app.pages.home import HomePage


async def main(page: ft.Page):
    page.title = "FaraidFlow"
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN)
    page.theme_mode = ft.ThemeMode.LIGHT

    prefs = ft.SharedPreferences()
    localization = await Localization.load(prefs, default_language="en")

    home = HomePage(page, localization)
    screen = {"name": "home"}
    calc = None

    def show_content(control):
        page.clean()
        page.add(control)
        page.update()

    def build_appbar():
        return home.build_appbar(on_change=on_language_changed)

    def on_language_changed():
        if screen["name"] == "calc" and calc is not None:
            refresh_calculate()
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

    home.on_calculate = show_calculate
    screen["name"] = "home"
    page.appbar = build_appbar()
    page.add(home.build())
    page.update()


if __name__ == "__main__":
    ft.run(main)