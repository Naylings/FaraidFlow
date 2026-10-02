"""Heir form builders for the calculate page."""

import flet as ft

from app.calculation import heirs

from .shared import (
    LABEL_WIDTH,
    MIN_CHECKBOX_WIDTH,
    MIN_FIELD_WIDTH,
    MIN_SPOUSE_INLINE_WIDTH,
    _label,
    _pairs,
)


def _heir_section(t, section, keys, controls, col_for, pane_width):
    """One titled block of the heir card. Spouse is a radio group plus the wife
    count; the other sections are paired count fields. Both go through here so
    the sections cannot drift apart."""
    if section == "spouse":
        # The wife count belongs beside the choice that enables it. It cannot
        # stay in one `wrap=True` row, because a wrapping child greedily takes
        # the full pane width and pushed the dropdown underneath at every size.
        # The pane decides instead: side by side while they fit, underneath when
        # they do not.
        if pane_width >= MIN_SPOUSE_INLINE_WIDTH:
            body = [ft.Row([controls["spouse"], controls["wife_count"]], spacing=12)]
        else:
            body = [controls["spouse"], controls["wife_count"]]
    else:
        body = [
            ft.ResponsiveRow(
                [_heir_field_row(t, k, controls, col_for) for k in pair],
                spacing=8,
                run_spacing=8,
            )
            for pair in _pairs(keys)
        ]
    return ft.Column(
        [
            ft.Text(
                t(f"calc.{section}"),
                size=13,
                weight=ft.FontWeight.BOLD,
            ),
            *body,
        ],
        spacing=8,
    )


def _heir_field_row(t, key, controls, col_for) -> ft.Row:
    if key in controls["parent_checkboxes"]:
        return ft.Row(
            [controls["parent_checkboxes"][key]],
            col=col_for(MIN_CHECKBOX_WIDTH),
        )
    field = controls["count_fields"][key]
    # expand so the entry takes exactly what the label leaves over and can never
    # push out past its own cell
    field.expand = True
    return ft.Row(
        [_label(t(key)), field],
        col=col_for(LABEL_WIDTH + MIN_FIELD_WIDTH),
        spacing=8,
    )


def build_heirs_card(t, on_spouse_change, col_for, pane_width) -> tuple[ft.Card, dict]:
    spouse = ft.RadioGroup(
        value="none",
        # wrap so the three choices break across lines on a narrow pane instead
        # of overflowing it
        content=ft.Row(
            [
                ft.Radio(value="none", label=t("calc.spouse_none")),
                ft.Radio(value="husband", label=t("husband")),
                ft.Radio(value="wife", label=t("wife"), tooltip=t("wife")),
            ],
            spacing=8,
            run_spacing=4,
            wrap=True,
        ),
        on_change=lambda e: on_spouse_change(),
    )
    wife_count = ft.Dropdown(
        key="count-wife",
        label=t("wife"),
        options=[ft.DropdownOption(key=str(n), content=ft.Text(str(n))) for n in range(1, 5)],
        value="1",
        width=110,
    )
    count_fields = {
        key: _count_field(key, t, show_label=False)
        for _, keys in heirs.HEIR_SECTIONS
        for key in keys
        if key not in ("husband", "wife", "father", "mother")
    }
    parent_checkboxes = {
        key: ft.Checkbox(key=key, label=t(key), value=False)
        for key in ("father", "mother")
    }
    controls = {
        "spouse": spouse,
        "wife_count": wife_count,
        "count_fields": count_fields,
        "parent_checkboxes": parent_checkboxes,
    }
    card = ft.Card(content=ft.Container(
        ft.Column([
            ft.Text(t("calc.heirs"), weight=ft.FontWeight.BOLD, size=15),
            ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
            *[
                _heir_section(t, section, keys, controls, col_for, pane_width)
                for section, keys in heirs.HEIR_SECTIONS
            ],
        ], spacing=16),
        padding=16,
    ))
    return card, controls


def _count_field(key, t, show_label=True):
    return ft.TextField(
        key=f"count-{key}",
        label=t(key) if show_label else None,
        value="0",
        width=110,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.InputFilter(
            regex_string=r"^[0-9]*$",
            allow=True,
            replacement_string="",
        ),
        on_change=lambda e: _keep_a_number(e.control),
    )


def _keep_a_number(field):
    """Same shape as _format_estate_field: a count is always one plain number,
    never blank, and never carrying stray characters."""
    digits = "".join(ch for ch in (field.value or "") if ch.isdigit())
    canonical = str(int(digits)) if digits else "0"
    if field.value != canonical:
        field.value = canonical
