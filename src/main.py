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

    def show_content(control):
        page.clean()
        page.add(control)
        page.update()

    def show_calculate():
        calc = CalculationPage(page, localization, back_home=lambda: show_content(home.build()))
        calc_page_root = calc.build()
        page.appbar = home.build_appbar()  # keep the language button visible
        show_content(calc_page_root)

    home.on_calculate = show_calculate
    page.appbar = home.build_appbar()
    page.add(home.build())
    page.update()


if __name__ == "__main__":
    ft.run(main)