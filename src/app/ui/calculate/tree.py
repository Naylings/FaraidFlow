"""Family-tree builders for the calculate page."""

import flet as ft

from app.calculation import heirs

from .shared import _chip_label, _empty_hint


def build_tree(t, heir_counts: dict, blocked: dict) -> ft.Card:
    branches = []
    for section, keys in heirs.HEIR_SECTIONS:
        present = {k: heir_counts.get(k, 0) for k in keys if heir_counts.get(k, 0) > 0}
        if not present:
            continue
        chips = ft.Column([
            ft.Chip(
                label=_chip_label(t(k) + (f" x{c}" if c > 1 else "")),
                bgcolor=ft.Colors.SURFACE_CONTAINER,
                disabled=k in blocked,
                tooltip=(
                    t("calc.blocked_tip").format(reason=t(blocked[k]))
                    if k in blocked
                    else t(k) + (f" x{c}" if c > 1 else "")
                ),
            )
            for k, c in present.items()
        ], spacing=4)
        # expand divides the container's real width between the branches, so
        # the split follows the result pane and not the window
        branches.append(ft.Column(
            [ft.Text(t(f"calc.{section}"), weight=ft.FontWeight.BOLD, size=12), chips],
            spacing=4,
            expand=1,
        ))
    root = ft.Chip(
        label=_chip_label(t("calc.deceased")),
        bgcolor=ft.Colors.PRIMARY_CONTAINER,
        tooltip=t("calc.deceased"),
    )
    # The tree fills the pane and shares it out by expand + gutter. Window
    # breakpoints cannot be used here: the tree sits inside the result pane,
    # which is only a fraction of the window, so a span set against the
    # window would squeeze three columns into half a window and collide.
    return ft.Card(content=ft.Container(
        ft.Column([
            ft.Text(t("calc.tree"), weight=ft.FontWeight.BOLD, size=15),
            ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
            root,
            ft.Row(
                branches,
                spacing=8,
                # A Row centres its children vertically by default, so a branch
                # with fewer chips floats up and its heading lands on a different
                # line from its neighbours'.
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ], spacing=10),
        padding=16,
        expand=True,
    ))


def build_empty_tree_card(t) -> ft.Card:
    return ft.Card(content=ft.Container(
        ft.Column([
            ft.Text(t("calc.tree"), weight=ft.FontWeight.BOLD, size=15),
            ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
            _empty_hint(t),
        ], spacing=10),
        padding=16,
        expand=True,
    ))
