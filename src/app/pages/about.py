# src/app/pages/about.py

import flet as ft

from app.localization.localization import Localization

# The about.* tables carry the row labels only; the facts beside them are the
# same in every language, so they are constants here.
APP_NAME = "FaraidFlow"
AUTHOR = "Naylings"
LOCATION = "Indonesia"
CREDITS = (
    "Built with Flet, Flutter and Python. The share rules follow the classical "
    "faraid sources (Qur'an, Sahih Bukhari, Sahih Muslim) and were cross-checked "
    "against BAZNAS's inheritance calculator for the Indonesian context."
)
LICENSE = "MIT"
GITHUB_URL = "https://github.com/Naylings/FaraidFlow"

# The rows below the app name, in reading order: (label key, value).
SECTIONS = [
    ("about.author", AUTHOR),
    ("about.location", LOCATION),
    ("about.credits", CREDITS),
    ("about.license", LICENSE),
    ("about.github", GITHUB_URL),
]


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
            controls=[header, self._app_line(), *self._sections(), self._donate()],
            spacing=16,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        return ft.SafeArea(content=column)

    def _app_line(self) -> ft.Text:
        return ft.Text(f"{APP_NAME} v{self.version}", size=18, weight=ft.FontWeight.BOLD)

    def _sections(self) -> list[ft.Column]:
        return [self._section(label_key, value) for label_key, value in SECTIONS]

    def _section(self, label_key: str, value: str) -> ft.Column:
        t = self.loc.get
        return ft.Column(
            controls=[
                ft.Text(t(label_key), size=20, weight=ft.FontWeight.BOLD),
                ft.Text(value),
            ],
            spacing=6,
        )

    def _donate(self) -> ft.FilledButton:
        """A placeholder, not a payment path: there is nowhere to send money yet,
        and a live-looking button that does nothing is worse than a disabled one."""
        t = self.loc.get
        return ft.FilledButton(
            content=t("about.donate"),
            key="about-donate",
            disabled=True,
            tooltip=t("about.donate_soon"),
        )
