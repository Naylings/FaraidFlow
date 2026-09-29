# src/app/pages/information.py

import flet as ft

from app.localization.localization import Localization

# Each glossary value is a whole "Term - definition" line, so it is rendered as
# one control; splitting it would let the term and its definition drift apart.
GLOSSARY_TERMS = ("wasiat", "hajb", "aul", "radd", "asabah", "pewaris", "ahli_waris")

# The five sections of the guide, in reading order: (title key, body keys).
SECTIONS = [
    ("info.intro.title", ["info.intro.body"]),
    ("info.legal_basis.title", ["info.legal_basis.quran", "info.legal_basis.hadith"]),
    ("info.how_it_works.title", ["info.how_it_works.body"]),
    ("info.glossary.title", [f"info.glossary.{term}" for term in GLOSSARY_TERMS]),
    ("info.disclaimer.title", ["info.disclaimer.body"]),
]


class InformationPage:
    """A read-only guide: what faraid is, its sources, and the terms it uses.

    Nothing here is computed, so build() is cheap and rebuilding it after a
    settings change is all that is needed to re-render it in another language.
    """

    def __init__(self, page, localization: Localization, back_home=None):
        self.page = page
        self.loc = localization
        self.back_home = back_home

    def build(self) -> ft.SafeArea:
        t = self.loc.get
        header = ft.Row([
            # Same key as the calculator's back button, so either screen's
            # back control is found the same way; calc.back is the only
            # "back" string the tables carry.
            ft.IconButton(ft.Icons.ARROW_BACK, key="back-home", tooltip=t("calc.back"), on_click=lambda e: self.back_home and self.back_home()),
            ft.Text(t("info.title"), size=22, weight=ft.FontWeight.BOLD),
        ])
        column = ft.Column(
            controls=[header, *self._sections()],
            spacing=16,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        return ft.SafeArea(content=column)

    def _sections(self) -> list[ft.Column]:
        return [self._section(title_key, body_keys) for title_key, body_keys in SECTIONS]

    def _section(self, title_key: str, body_keys: list[str]) -> ft.Column:
        t = self.loc.get
        return ft.Column(
            controls=[
                ft.Text(t(title_key), size=20, weight=ft.FontWeight.BOLD),
                *[ft.Text(t(key)) for key in body_keys],
            ],
            spacing=6,
        )
