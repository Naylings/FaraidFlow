"""Claims notices for the calculate page."""

import flet as ft


def build_claims(t, result, heirs, estate, fmt) -> ft.Column | None:
    claims = []
    if result.errors:
        prioritized = [e for e in result.errors if e == "calc.errors.no_heirs"] or result.errors
        for e in prioritized:
            claims.append(ft.Text(t(e), color=ft.Colors.ERROR))
    if estate.has_numbers and estate.unpaid > 0 and not result.errors:
        claims.append(ft.Text(t("calc.debt_note"), italic=True, size=12))
    if not result.errors and estate.net <= 0 and estate.has_numbers:
        if estate.unpaid > 0:
            claims.append(ft.Text(
                t("calc.depleted").format(amount=fmt(estate.unpaid)),
                color=ft.Colors.ERROR,
            ))
        else:
            claims.append(ft.Text(t("calc.nothing"), color=ft.Colors.ERROR))
    if claims:
        return ft.Column(claims, spacing=6)
    return None
