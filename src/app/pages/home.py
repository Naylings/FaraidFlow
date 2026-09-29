# src/app/pages/home.py

import flet as ft

from app.components.settings_button import SettingsButton
from app.localization.localization import Localization

MENU = [
    ("calculate", ft.Icons.CALCULATE),
    ("information", ft.Icons.BOOK),
    ("about", ft.Icons.INFO),
]


class HomePage:
    def __init__(self, page: ft.Page, localization: Localization, on_calculate=None, on_information=None, on_about=None):
        self.page = page
        self.localization = localization
        self.on_calculate = on_calculate
        self.on_information = on_information
        self.on_about = on_about
        self._extra_actions: list = []
        self.body = self.build_body()

    def build_appbar(self, on_change=None, extra_actions: list | None = None) -> ft.AppBar:
        # remembered so refresh() can rebuild the same bar; without this the
        # Calculate action would silently vanish on any refresh that relies on
        # the default on_change (this method is that default).
        self._extra_actions = list(extra_actions or [])
        settings_button = SettingsButton(
            page=self.page,
            localization=self.localization,
            on_change=on_change or self.refresh,
        )
        return ft.AppBar(
            title=ft.Text(self.localization.get("home.title")),
            actions=[settings_button.button, *self._extra_actions],
        )

    def build_body(self) -> ft.Column:
        t = self.localization.get
        buttons = [
            ft.FilledButton(
                content=t(key),
                icon=icon,
                key=f"menu-{key}",
                width=260,
                height=48,
                on_click=lambda e, k=key: self._dispatch(k),
            )
            for key, icon in MENU
        ]
        return ft.Column(
            controls=[
                ft.Text(t("home.title"), size=32, weight=ft.FontWeight.BOLD),
                ft.Text(t("home.subtitle"), size=18, italic=True),
                ft.Container(height=16),
                *buttons,
                ft.Text("v0.1", size=12),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def build(self):
        return ft.SafeArea(content=self.body)

    def refresh(self) -> None:
        self.body = self.build_body()
        self.page.appbar = self.build_appbar(extra_actions=self._extra_actions)
        self.page.clean()
        self.page.add(self.build())
        self.page.update()

    def _dispatch(self, key: str) -> None:
        """Send a menu button to its page; a screen whose callback has not been
        passed in does nothing."""
        handler = {
            "calculate": self.on_calculate,
            "information": self.on_information,
            "about": self.on_about,
        }.get(key)
        if handler is not None:
            handler()