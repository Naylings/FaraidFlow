"""Estate form builder for the calculate page."""

import flet as ft


def build_estate_card(t, format_field) -> tuple[ft.Card, dict[str, ft.TextField]]:
    tfs = {
        k: ft.TextField(
            key=k,
            label=t({"estate-gross": "calc.gross", "estate-funeral": "calc.funeral", "estate-debts": "calc.debts", "estate-wasiat": "calc.wasiat"}[k]),
            value="0",
            width=180,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(
                regex_string=r"^[0-9,]*$",
                allow=True,
                replacement_string="",
            ),
            on_change=lambda e, k=k: format_field(k),
        )
        for k in ("estate-gross", "estate-funeral", "estate-debts", "estate-wasiat")
    }
    card = ft.Card(content=ft.Container(
        ft.Column([
            ft.Text(t("calc.estate"), weight=ft.FontWeight.BOLD, size=15),
            ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
            ft.Row(list(tfs.values()), wrap=True),
        ], spacing=16),
        padding=16,
    ))
    return card, tfs
