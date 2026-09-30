# src/app/components/settings_button.py

import flet as ft

from app.localization.localization import CURRENCIES, LANGUAGES, THEMES


class SettingsButton:
    """AppBar button that opens a summary settings dialog.

    The summary lists each setting (language, currency, theme) with its
    current value; tapping a value opens a single-choice dialog for that
    setting. Picking an option persists it immediately, closes the choice
    dialog, refreshes the summary and calls on_change() so the app can
    re-render with the new value. The summary stays open throughout.
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
        self._labels = {
            "language": t("settings.language"),
            "currency": t("settings.currency"),
            "theme": t("settings.theme"),
        }
        self._options = {
            "language": self._option_tuples_language(),
            "currency": self._option_tuples_currency(),
            "theme": self._option_tuples_theme(),
        }
        self._value_buttons = {}
        rows = []
        for code in ("language", "currency", "theme"):
            button = ft.TextButton(
                content=self._current_label(code),
                key=f"setting-value-{code}",
                on_click=self._make_choice_handler(code),
            )
            self._value_buttons[code] = button
            rows.append(ft.Row([ft.Text(self._labels[code]), button], spacing=8))
        self._dialog = ft.AlertDialog(
            title=ft.Text(t("settings.title")),
            content=ft.Column(rows, spacing=4),
        )
        self.page.show_dialog(self._dialog)

    def _current_label(self, code: str) -> str:
        """Display label of the current value, from the same tuples the choice
        dialogs use — one source, so summary and choice can never disagree."""
        current = {
            "language": self.localization.language,
            "currency": self.localization.currency,
            "theme": self.localization.theme,
        }[code]
        for value, _key, label in self._options[code]:
            if value == current:
                return label
        return current

    def _make_choice_handler(self, code: str):
        async def _handle(e):
            self._open_choice(code)

        return _handle

    def _open_choice(self, code: str) -> None:
        current = {
            "language": self.localization.language,
            "currency": self.localization.currency,
            "theme": self.localization.theme,
        }[code]
        choose = {
            "language": self.choose_language,
            "currency": self.choose_currency,
            "theme": self.choose_theme,
        }[code]
        tiles = self._option_page(self._options[code], current, choose).controls
        choice = ft.AlertDialog(
            title=ft.Text(self._labels[code]),
            # Bounded so the 5-entry currency list cannot grow the dialog; scrolls
            # on short screens. Pixel heights are not test-pinned — structure is.
            content=ft.Column(height=320, scroll=ft.ScrollMode.AUTO, controls=tiles),
        )
        self.page.show_dialog(choice)

    def _option_tuples_language(self) -> list:
        return [
            (lang["code"], f"lang-{lang['code']}", f'{lang["flag"]} {lang["label"]}')
            for lang in LANGUAGES
        ]

    def _option_tuples_currency(self) -> list:
        t = self.localization.get
        return [
            (
                currency["code"],
                f"currency-{currency['code'].lower()}",
                t("currency." + currency["code"].lower()),
            )
            for currency in CURRENCIES
        ]

    def _option_tuples_theme(self) -> list:
        t = self.localization.get
        return [
            (theme["code"], f"theme-{theme['code']}", t(theme["label_key"]))
            for theme in THEMES
        ]

    def _language_page(self) -> ft.ListView:
        return self._option_page(
            self._option_tuples_language(),
            self.localization.language,
            self.choose_language,
        )

    def _currency_page(self) -> ft.ListView:
        return self._option_page(
            self._option_tuples_currency(),
            self.localization.currency,
            self.choose_currency,
        )

    def _theme_page(self) -> ft.ListView:
        return self._option_page(
            self._option_tuples_theme(),
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
        self._picked("language")

    async def choose_currency(self, code: str) -> None:
        await self.localization.set_currency(code)
        self._picked("currency")

    async def choose_theme(self, code: str) -> None:
        await self.localization.set_theme(code)
        self._picked("theme")

    def _picked(self, code: str) -> None:
        # pop_dialog removes the top of the stack — the choice dialog. The
        # summary underneath stays open.
        self.page.pop_dialog()
        self._value_buttons[code].content = self._current_label(code)
        # page.update pushes to a live page; FakePage absorbs it. Never
        # dialog.update() — it raises RuntimeError when unmounted (tests).
        self.page.update(self._dialog)
        if self.on_change is not None:
            self.on_change()
