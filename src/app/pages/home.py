# src/app/pages/home.py

import flet as ft

from app.components.language_button import LanguageButton
from app.localization.localization import Localization

MENU = [
    ("calculate", ft.Icons.CALCULATE),
    ("information", ft.Icons.BOOK),
    ("about", ft.Icons.INFO),
]


class HomePage:
    def __init__(self, page: ft.Page, localization: Localization, on_calculate=None):
        self.page = page
        self.localization = localization
        self.on_calculate = on_calculate
        self.body = self.build_body()

    def build_appbar(self, on_change=None) -> ft.AppBar:
        lang_button = LanguageButton(
            page=self.page,
            localization=self.localization,
            on_change=on_change or self.refresh,
        )
        return ft.AppBar(
            title=ft.Text(self.localization.get("home.title")),
            actions=[lang_button.button],
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
                on_click=lambda e, k=key: (self.on_calculate() if k == "calculate" and self.on_calculate else self._show_soon(k)),
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
        self.page.appbar = self.build_appbar()
        self.page.clean()
        self.page.add(self.build())
        self.page.update()

    def _show_soon(self, section: str) -> None:
        self.page.show_dialog(
            ft.SnackBar(content=self.localization.get(f"soon.{section}"))
        )