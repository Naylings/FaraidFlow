"""Details tile and notes builders for the calculate page."""

import math

import flet as ft

from .shared import _empty_hint, _fmt_num, _inset


def _equivalence_lines(rows) -> list[str]:
    if not rows:
        return []
    lcm = 1
    for row in rows:
        lcm = math.lcm(lcm, (row.share * row.count).denominator)
    out = []
    for row in rows:
        group = row.share * row.count
        num = group * lcm
        out.append(f"{_fmt_num(group)} = {num.numerator}/{lcm}")
    return out


def build_details(t, result, estate, fmt) -> ft.Container:
    eq = _equivalence_lines(result.rows)
    controls = []
    for row, line in zip(result.rows, eq):
        label = t(row.key) + (f" x{row.count}" if row.count > 1 else "")
        controls.append(_detail_row(label, line))
    if controls and result.unassigned is None:
        lcm = 1
        for row in result.rows:
            lcm = math.lcm(lcm, (row.share * row.count).denominator)
        total_num = sum(row.share * row.count for row in result.rows) * lcm
        controls.append(_detail_gap())
        controls.append(ft.Text(
            f"{total_num.numerator}/{lcm} = 1",
            size=12,
            weight=ft.FontWeight.BOLD,
        ))
    if result.blocked_reasons:
        if controls:
            controls.append(_detail_gap())
        controls.append(ft.Text(
            t("calc.blocked") + ":", size=12, weight=ft.FontWeight.BOLD,
        ))
        controls.extend(
            ft.Text(f"{t(k)} - {t(reason)}", size=12)
            for k, reason in result.blocked_reasons.items()
        )
    if estate.has_numbers and result.residual != 0 and result.unassigned is None:
        if controls:
            controls.append(_detail_gap())
        controls.append(ft.Text(
            t("calc.residual").format(amount=fmt(result.residual)), size=12,
        ))
    if not controls:
        controls.append(_empty_hint(t))
    return ft.Container(
        ft.ExpansionTile(
            key="calc-details",
            title=ft.Text(t("calc.details")),
            controls=controls,
            expanded=False,
        ),
        # same inset as the table above it and the tree card, so all three
        # blocks start on the same left edge
        padding=ft.Padding.only(left=16, right=16),
    )


def _detail_gap() -> ft.Divider:
    return ft.Divider(height=9, color=ft.Colors.OUTLINE_VARIANT)


def _detail_row(label, value):
    """One heir on a row, shares aligned in their own column so the numbers
    line up instead of running together inside a single wrapped blob."""
    return ft.Row([
        ft.Text(label, size=12, expand=4, no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS, tooltip=label),
        ft.Text(value, size=12, expand=3, text_align=ft.TextAlign.RIGHT,
                no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, tooltip=value),
    ], spacing=8)


def build_notes(t, result) -> ft.Container:
    notes = []
    if result.aul:
        notes.append(t("calc.aul").format(old=result.base_from, new=result.base))
    if result.radd_applied:
        notes.append(t("calc.radd"))
    if result.asabah_keys:
        names = ", ".join(t(k) for k in result.asabah_keys)
        notes.append(t("calc.asabah").format(names=names))
    if result.unassigned is not None:
        notes.append(t("calc.unassigned"))
    if not notes:
        return _inset(ft.Column([], spacing=0))
    return _inset(
        ft.Column([ft.Text("\n".join(f"• {n}" for n in notes), size=12, italic=True)], spacing=0)
    )
