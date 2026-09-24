import flet as ft

from app.localization.localization import Localization
from app.pages.home import HomePage


async def main(page: ft.Page):
    page.title = "FaraidFlow"
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN)
    page.theme_mode = ft.ThemeMode.LIGHT

    prefs = ft.SharedPreferences()
    localization = await Localization.load(prefs, default_language="en")

    home = HomePage(page, localization)
    page.appbar = home.build_appbar()
    page.add(home.build())
    page.update()


if __name__ == "__main__":
    ft.run(main)