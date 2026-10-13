# src/app/pages/about.py

import flet as ft

from app.localization.localization import Localization

# The about.* tables carry the row labels only; the facts beside them are the
# same in every language, so they are constants here.
APP_NAME = "FaraidFlow"
AUTHOR = "Muhammad Naya Dzulqornain"
LOCATION = "Indonesia"
LICENSE = "MIT"
GITHUB_URL = "https://github.com/Naylings/FaraidFlow"

# The rows below the identity header, in reading order. The credits value is
# per-language, so it is resolved in AboutPage._rows instead of living in a
# module constant. Icons ride along so the card task needs no second source
# of truth.


class AboutPage:
    """Who made this, what it is built on, and where to find it.

    Nothing here is computed, so build() is cheap and rebuilding it after a
    settings change is all that is needed to re-render it in another language.
    """

    def __init__(self, page, localization: Localization, back_home=None, *, version: str):
        self.page = page
        self.loc = localization
        self.back_home = back_home
        self.version = version

    def build(self) -> ft.SafeArea:
        t = self.loc.get
        header = ft.Row([
            # Same key as the calculator's back button, so any screen's back
            # control is found the same way; calc.back is the only "back" string
            # the tables carry.
            ft.IconButton(ft.Icons.ARROW_BACK, key="back-home", tooltip=t("calc.back"), on_click=lambda e: self.back_home and self.back_home()),
            ft.Text(t("about.title"), size=22, weight=ft.FontWeight.BOLD),
        ])
        column = ft.Column(
            controls=[header, self._identity(), *self._sections()],
            spacing=16,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        return ft.SafeArea(content=column)

    def _identity(self) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Image(
                        src="assets/icon.png",
                        key="about-logo",
                        width=96,
                        height=96,
                        fit=ft.BoxFit.CONTAIN,
                        border_radius=ft.BorderRadius.all(48),
                        error_content=ft.Icon(ft.Icons.INFO),
                        semantics_label="FaraidFlow logo",
                    ),
                    ft.Text(APP_NAME, size=26, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Text(f"v{self.version}", key="about-version", size=14),
                        padding=ft.Padding.symmetric(horizontal=12, vertical=4),
                        border_radius=ft.BorderRadius.all(12),
                        bgcolor=ft.Colors.SURFACE_CONTAINER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
        )

    def _sections(self) -> list[ft.Card]:
        t = self.loc.get
        return [self._card(label_key, icon, value) for label_key, icon, value in self._rows(t)]

    def _rows(self, t):
        """(label key, icon, value) in reading order. Icons ride along so the
        card task needs no second source of truth."""
        return [
            ("about.author", ft.Icons.PERSON, AUTHOR),
            ("about.location", ft.Icons.LOCATION_ON, LOCATION),
            ("about.credits", ft.Icons.BOOK, t("about.credits.body")),
            ("about.license", ft.Icons.GAVEL, LICENSE),
            ("about.github", ft.Icons.CODE, GITHUB_URL),
        ]

    def _card(self, label_key: str, icon, value: str) -> ft.Card:
        t = self.loc.get
        return ft.Card(
            content=ft.ListTile(
                leading=ft.Icon(icon),
                title=ft.Text(t(label_key), weight=ft.FontWeight.BOLD, size=18),
                subtitle=ft.Text(value),
            ),
        )
