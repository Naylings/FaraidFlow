# src/app/components/settings_button.py

import flet as ft

from app.localization.localization import CURRENCIES, LANGUAGES, THEMES


class SettingsButton:
    """AppBar button that opens a stacked master/detail settings dialog.

    Each category (language, currency, theme) is a single-choice list: picking an
    option persists it immediately, closes the dialog and calls on_change() so
    the app can re-render with the new value.
    """

    def __init__(self, page, localization, on_change):
        self.page = page
        self.localization = localization
        self.on_change = on_change

        self.button = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            key="settings-button",
            tooltip=self.localization.get("settings.title"),
            on_click=lambda e: self.open(),
        )

    def open(self) -> None:
        t = self.localization.get
        self._category = "language"
        self._pages = {
            "language": self._language_page(),
            "currency": self._currency_page(),
            "theme": self._theme_page(),
        }
        self._labels = {
            "language": t("settings.language"),
            "currency": t("settings.currency"),
            "theme": t("settings.theme"),
        }
        self._detail = ft.Container(key="settings-detail", content=self._pages[self._category], expand=True)
        dialog = ft.AlertDialog(
            title=ft.Text(t("settings.title")),
            content=ft.Column(
                height=360,
                controls=[self._category_row(), self._detail],
            ),
        )
        self._dialog = dialog
        self.page.show_dialog(dialog)

    def _category_row(self) -> ft.Row:
        self._tiles = {}
        tiles = []
        for code in ("language", "currency", "theme"):
            tile = self._category_tile(code)
            self._tiles[code] = tile
            tiles.append(tile)
        return ft.Row(tiles, spacing=8)

    def _category_tile(self, code: str) -> ft.ListTile:
        return ft.ListTile(
            key=f"cat-{code}",
            title=ft.Text(self._labels[code]),
            trailing=ft.Icon(ft.Icons.CHECK) if code == self._category else None,
            on_click=self._make_category_handler(code),
        )

    def _make_category_handler(self, code: str):
        async def _handle(e):
            self._category = code
            self._detail.content = self._pages[code]
            for tile in self._tiles.values():
                tile.trailing = ft.Icon(ft.Icons.CHECK) if tile.key == f"cat-{code}" else None
            # page.update pushes to a live page; FakePage absorbs it. Never
            # dialog.update() — it raises RuntimeError when unmounted (tests).
            self.page.update(self._dialog)

        return _handle

    def _language_page(self) -> ft.ListView:
        return self._option_page(
            [
                (lang["code"], f"lang-{lang['code']}", f'{lang["flag"]} {lang["label"]}')
                for lang in LANGUAGES
            ],
            self.localization.language,
            self.choose_language,
        )

    def _currency_page(self) -> ft.ListView:
        t = self.localization.get
        return self._option_page(
            [
                (
                    currency["code"],
                    f"currency-{currency['code'].lower()}",
                    t("currency." + currency["code"].lower()),
                )
                for currency in CURRENCIES
            ],
            self.localization.currency,
            self.choose_currency,
        )

    def _theme_page(self) -> ft.ListView:
        t = self.localization.get
        return self._option_page(
            [
                (theme["code"], f"theme-{theme['code']}", t(theme["label_key"]))
                for theme in THEMES
            ],
            self.localization.theme,
            self.choose_theme,
        )

    def _option_page(self, options, current: str, select) -> ft.ListView:
        """One scrollable list of `options`, each a (code, key, label) tuple."""
        return ft.ListView(
            expand=True,
            controls=[
                ft.ListTile(
                    key=key,
                    title=ft.Text(label),
                    trailing=ft.Icon(ft.Icons.CHECK) if code == current else None,
                    on_click=self._make_handler(select, code),
                )
                for code, key, label in options
            ],
        )

    @staticmethod
    def _make_handler(select, code: str):
        async def _handle(e):
            await select(code)

        return _handle

    async def choose_language(self, code: str) -> None:
        await self.localization.set_language(code)
        self._chosen()

    async def choose_currency(self, code: str) -> None:
        await self.localization.set_currency(code)
        self._chosen()

    async def choose_theme(self, code: str) -> None:
        await self.localization.set_theme(code)
        self._chosen()

    def _chosen(self) -> None:
        self.page.pop_dialog()
        if self.on_change is not None:
            self.on_change()
