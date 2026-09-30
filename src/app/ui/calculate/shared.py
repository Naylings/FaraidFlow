"""Shared UI helpers for the calculate page."""

import flet as ft


def _fmt_int(n: int) -> str:
    return f"{n:,}"


def _parse_int(text: str) -> int:
    try:
        return int("".join(ch for ch in (text or "") if ch.isdigit()) or "0")
    except ValueError:
        return 0


LABEL_WIDTH = 150
GUTTER = 8
CARD_PADDING = 16
# Narrowest entry still worth showing next to a 150px label. This is a comfort
# threshold, not a correctness one: the field carries `expand`, so it can never
# overflow its cell whatever this is set to. Below it the two fields would leave
# the entry around 60-90px, which is too cramped to type into.
MIN_FIELD_WIDTH = 100
# A parent row is only a checkbox and its own short label, so it needs far less
# than a 150px text label plus an entry. Using the text-field threshold for it
# stacked the parents on a phone even though they fitted side by side.
MIN_CHECKBOX_WIDTH = 130
# The three spouse radios side by side with the dropdown need roughly 400px of
# pane. Below that the dropdown goes underneath. Deliberately a little generous:
# overshooting only puts the dropdown under the radios on a medium screen, while
# undershooting would cut it off screen. The radios wrap regardless, so a
# misjudged threshold can never overflow.
MIN_SPOUSE_INLINE_WIDTH = 420


def _label(text: str) -> ft.Text:
    return ft.Text(
        text,
        width=LABEL_WIDTH,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS,
    )


TWO_PANE_MIN_WIDTH = 992


def is_two_pane(width) -> bool:
    return width is not None and width >= TWO_PANE_MIN_WIDTH


def _pairs(keys):
    return [tuple(keys[i:i + 2]) for i in range(0, len(keys), 2)]


def _fmt_num(frac) -> str:
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def _chip_label(value: str) -> ft.Text:
    """Chip text must never spill past its column and overlap a neighbour."""
    return ft.Text(value, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS)


def _inset(block: ft.Control) -> ft.Container:
    """Same 16px left/right inset the table, the tree card and the details tile
    use, so every block in the result pane starts on the same left edge. The
    estate arithmetic line was the last one still running to the bezel."""
    return ft.Container(block, padding=ft.Padding.only(left=16, right=16))


def _empty_hint(t) -> ft.Text:
    """One shared clarification line for blocks with no data yet."""
    return ft.Text(t("calc.empty_hint"), size=12, italic=True)


def format_amount(loc, value) -> str:
    """One amount, in whichever currency settings picked.

    Every amount on this page goes through here, so there is a single money
    formatter in the app: Localization's. A result with no numbers entered
    carries no amount at all for the per-person and total columns, and that
    has always shown as a dash rather than a number.
    """
    return "-" if value is None else loc.format_money(value)


def _cell(value, weight, bold=False, numeric=False):
    return ft.Text(
        value,
        size=12,
        weight=ft.FontWeight.BOLD if bold else None,
        expand=weight,
        text_align=ft.TextAlign.RIGHT if numeric else ft.TextAlign.LEFT,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS,
        tooltip=value,
    )
