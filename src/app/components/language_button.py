# src/app/components/language_button.py

import flet as ft

from app.localization.localization import LANGUAGES


class LanguageButton:
    def __init__(self, page, localization, on_change):
        self.page = page
        self.localization = localization
        self.on_change = on_change

        self.button = ft.TextButton(
            content=self._flag_text(),
            key="lang-button",
            tooltip=self.localization.get("language.tooltip"),
            on_click=lambda e: self.open(),
        )

    def _flag_text(self) -> str:
        for lang in LANGUAGES:
            if lang["code"] == self.localization.language:
                return f'{lang["flag"]} {lang["code"].upper()}'
        return self.localization.language

    def open(self) -> None:
        dialog = ft.AlertDialog(
            title=ft.Text(self.localization.get("language.title")),
            content=ft.Column([self._option(lang) for lang in LANGUAGES]),
        )
        self.page.show_dialog(dialog)

    def _option(self, lang: dict) -> ft.ListTile:
        return ft.ListTile(
            key=f"lang-{lang['code']}",
            title=ft.Text(f'{lang["flag"]} {lang["label"]}'),
            trailing=ft.Icon(ft.Icons.CHECK)
            if lang["code"] == self.localization.language
            else None,
            on_click=self._make_handler(lang["code"]),
        )

    def _make_handler(self, code: str):
        async def _handle(e):
            await self.choose(code)

        return _handle

    async def choose(self, code: str) -> None:
        await self.localization.set_language(code)
        self.page.pop_dialog()
        if self.on_change is not None:
            self.on_change()