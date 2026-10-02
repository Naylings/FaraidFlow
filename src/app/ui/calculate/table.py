"""Result-table and estate-breakdown builders for the calculate page."""

import flet as ft

from .shared import _cell, _empty_hint, _fmt_num, _inset


def build_result_table(t, rows, fmt) -> ft.Container:
    if rows:
        show_each = any(row.count > 1 for row in rows)
        weights = [("calc.col_heir", 3), ("calc.col_share", 2)]
        if show_each:
            weights.append(("calc.col_each", 2))
        weights.append(("calc.col_total", 2))

        table_rows = [
            ft.Row(
                [_cell(t(key), w, bold=True, numeric=idx > 0) for idx, (key, w) in enumerate(weights)],
                spacing=8,
            ),
            ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
        ]
        for row in rows:
            cells = [
                _cell(
                    t(row.key) + (f"  x{row.count}" if row.count > 1 else ""),
                    weights[0][1],
                ),
                _cell(_fmt_num(row.share * row.count), weights[1][1], numeric=True),
            ]
            if show_each:
                cells.append(_cell(fmt(row.each), weights[2][1], numeric=True))
            cells.append(
                _cell(
                    fmt(row.amount),
                    weights[-1][1],
                    numeric=True,
                )
            )
            table_rows.append(ft.Row(cells, spacing=8))
        return ft.Container(
            ft.Column(table_rows, key="result-table", spacing=6),
            # keep the amounts off the card bezel, matching the tree card's inset
            padding=ft.Padding.only(left=16, right=16),
        )
    cols = [("calc.col_heir", 3, False), ("calc.col_share", 2, True), ("calc.col_total", 2, True)]
    header = ft.Row(
        [
            ft.Text(
                t(key),
                size=12,
                weight=ft.FontWeight.BOLD,
                expand=w,
                text_align=ft.TextAlign.RIGHT if numeric else ft.TextAlign.LEFT,
                no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS,
                tooltip=t(key),
            )
            for key, w, numeric in cols
        ],
        spacing=8,
    )
    return ft.Container(
        ft.Column([header, ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT), _empty_hint(t)], key="result-table", spacing=6),
        padding=ft.Padding.only(left=16, right=16),
    )


def build_breakdown(t, estate, fmt) -> ft.Container:
    e = estate
    line = (
        f"{t('calc.gross')} {fmt(e.gross)} - "
        f"{t('calc.funeral')} {fmt(e.funeral)} - "
        f"{t('calc.debts')} {fmt(e.debts)} - "
        f"{t('calc.wasiat')} {fmt(e.wasiat)} = "
        f"{t('calc.net')} {fmt(e.net)}"
    )
    rows = [ft.Text(line, size=12)]
    if not e.wasiat_ok:
        rows.append(ft.Text(
            f"{t('calc.wasiat_warn')} {t('calc.wasiat_cap')} {fmt(e.wasiat_cap)}"
            f", {t('calc.wasiat_exc')} {fmt(e.wasiat_excess)}"
            f"; {t('calc.wasiat_consent')}",
            size=12,
            italic=True,
        ))
    return _inset(ft.Column(rows, spacing=4))
