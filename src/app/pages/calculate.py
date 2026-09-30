# src/app/pages/calculate.py

import asyncio
import math

import flet as ft

from app.calculation import engine, heirs
from app.calculation import estate as estate_mod
from app.localization.localization import Localization
from app.ui.calculate.shared import (
    CARD_PADDING,
    GUTTER,
    LABEL_WIDTH,
    MIN_CHECKBOX_WIDTH,
    MIN_FIELD_WIDTH,
    MIN_SPOUSE_INLINE_WIDTH,
    _cell,
    _chip_label,
    _empty_hint,
    _fmt_int,
    _fmt_num,
    _inset,
    _label,
    _pairs,
    _parse_int,
    format_amount,
    is_two_pane,
)


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


class CalculationPage:
    def __init__(self, page, localization: Localization, back_home=None):
        self.page = page
        self.loc = localization
        self.back_home = back_home
        self.heirs: dict[str, int] = {}
        self.estate = estate_mod.Estate()
        self.calc_result: engine.Result | None = None
        self.result_card = ft.Column(spacing=12, key=ft.ScrollKey("result-card"))
        self._parent_checkboxes: dict[str, ft.Checkbox] = {}
        self._root = None
        self.two_pane = is_two_pane(getattr(page, "width", None))
        self._scroll_host = None

    def _num(self, control_key, default_text="0"):
        tf = self._tf[control_key]
        return _parse_int(tf.value or default_text)

    def _format_estate_field(self, key):
        tf = self._tf[key]
        digits = _parse_int(tf.value)
        grouped = _fmt_int(digits)
        if tf.value != grouped:
            tf.value = grouped

    def _count_of(self, field) -> int:
        try:
            return max(0, int(field.value or 0))
        except (TypeError, ValueError):
            return 0

    def _sync_wife_count(self):
        self._wife_count.disabled = self._spouse.value != "wife"

    def _slot_from_inputs(self) -> dict[str, int]:
        h = {}
        if self._spouse.value == "husband":
            h["husband"] = 1
        elif self._spouse.value == "wife":
            h["wife"] = max(1, self._count_of(self._wife_count))
        for key, field in self._count_fields.items():
            v = self._count_of(field)
            if v:
                h[key] = v
        for key, cb in self._parent_checkboxes.items():
            if cb.value:
                h[key] = 1
        return h

    def _estate_from_inputs(self) -> estate_mod.Estate:
        return estate_mod.Estate(
            gross=self._num("estate-gross"),
            funeral=self._num("estate-funeral"),
            debts=self._num("estate-debts"),
            wasiat=self._num("estate-wasiat"),
        )

    def _collect(self):
        self.heirs = heirs.normalize(self._slot_from_inputs())
        self.estate = self._estate_from_inputs()

    def _compute(self):
        self.calc_result = engine.resolve(
            self.heirs,
            estate=self.estate if self.estate.has_numbers else None,
        )
        self.result_card.controls = [self._build_result()]

    def capture_state(self):
        if not hasattr(self, "_tf"):
            return None
        return {
            "tf": {k: tf.value for k, tf in self._tf.items()},
            "spouse": self._spouse.value,
            "wife_count": self._wife_count.value,
            "counts": {k: f.value for k, f in self._count_fields.items()},
            "parents": {k: cb.value for k, cb in self._parent_checkboxes.items()},
            "has_result": bool(self.result_card.controls),
        }

    def restore_state(self, state):
        if state is None:
            return
        for k, v in state["tf"].items():
            if k in self._tf:
                self._tf[k].value = v
        self._spouse.value = state["spouse"]
        self._sync_wife_count()
        self._wife_count.value = state["wife_count"]
        for k, v in state["counts"].items():
            if k in self._count_fields:
                self._count_fields[k].value = v
        for k, v in (state.get("parents") or {}).items():
            if k in self._parent_checkboxes:
                self._parent_checkboxes[k].value = v
        if state.get("has_result"):
            self._collect()
            self._compute()

    def _build_tree(self) -> ft.Card:
        t = self.loc.get
        blocked = getattr(self.calc_result, "blocked_reasons", {}) or {}
        branches = []
        for section, keys in heirs.HEIR_SECTIONS:
            present = {k: self.heirs.get(k, 0) for k in keys if self.heirs.get(k, 0) > 0}
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

    def _build_result(self) -> ft.Column:
        r = self.calc_result
        t = self.loc.get
        blocks = []

        if not r.errors and self.heirs:
            blocks.append(self._build_tree())
        else:
            blocks.append(self._empty_tree_card())

        claims = []
        if r.errors:
            prioritized = [e for e in r.errors if e == "calc.errors.no_heirs"] or r.errors
            for e in prioritized:
                claims.append(ft.Text(t(e), color=ft.Colors.ERROR))
        if self.estate.has_numbers and self.estate.unpaid > 0 and not r.errors:
            claims.append(ft.Text(t("calc.debt_note"), italic=True, size=12))
        if not r.errors and self.estate.net <= 0 and self.estate.has_numbers:
            if self.estate.unpaid > 0:
                claims.append(ft.Text(
                    t("calc.depleted").format(amount=format_amount(self.loc, self.estate.unpaid)),
                    color=ft.Colors.ERROR,
                ))
            else:
                claims.append(ft.Text(t("calc.nothing"), color=ft.Colors.ERROR))

        if claims:
            blocks.append(ft.Column(claims, spacing=6))

        if r.rows:
            t2 = self.loc.get
            show_each = any(row.count > 1 for row in r.rows)
            weights = [("calc.col_heir", 3), ("calc.col_share", 2)]
            if show_each:
                weights.append(("calc.col_each", 2))
            weights.append(("calc.col_total", 2))

            table_rows = [
                ft.Row(
                    [_cell(t2(key), w, bold=True, numeric=idx > 0) for idx, (key, w) in enumerate(weights)],
                    spacing=8,
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
            ]
            for row in r.rows:
                cells = [
                    _cell(
                        t2(row.key) + (f"  x{row.count}" if row.count > 1 else ""),
                        weights[0][1],
                    ),
                    _cell(_fmt_num(row.share * row.count), weights[1][1], numeric=True),
                ]
                if show_each:
                    cells.append(_cell(format_amount(self.loc, row.each), weights[2][1], numeric=True))
                cells.append(
                    _cell(
                        format_amount(self.loc, row.amount),
                        weights[-1][1],
                        numeric=True,
                    )
                )
                table_rows.append(ft.Row(cells, spacing=8))
            blocks.append(ft.Container(
                ft.Column(table_rows, key="result-table", spacing=6),
                # keep the amounts off the card bezel, matching the tree card's inset
                padding=ft.Padding.only(left=16, right=16),
            ))
            blocks.append(self._build_breakdown())
            blocks.append(self._build_notes())
        else:
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
            blocks.append(ft.Container(
                ft.Column([header, ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT), _empty_hint(t)], key="result-table", spacing=6),
                padding=ft.Padding.only(left=16, right=16),
            ))
        blocks.append(self._build_details(r))

        return ft.Column(
            controls=blocks,
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _build_breakdown(self) -> ft.Column:
        e = self.estate
        t = self.loc.get
        line = (
            f"{t('calc.gross')} {format_amount(self.loc, e.gross)} - "
            f"{t('calc.funeral')} {format_amount(self.loc, e.funeral)} - "
            f"{t('calc.debts')} {format_amount(self.loc, e.debts)} - "
            f"{t('calc.wasiat')} {format_amount(self.loc, e.wasiat)} = "
            f"{t('calc.net')} {format_amount(self.loc, e.net)}"
        )
        rows = [ft.Text(line, size=12)]
        if not e.wasiat_ok:
            rows.append(ft.Text(
                f"{t('calc.wasiat_warn')} {t('calc.wasiat_cap')} {format_amount(self.loc, e.wasiat_cap)}"
                f", {t('calc.wasiat_exc')} {format_amount(self.loc, e.wasiat_excess)}"
                f"; {t('calc.wasiat_consent')}",
                size=12,
                italic=True,
            ))
        return _inset(ft.Column(rows, spacing=4))

    def _build_notes(self) -> ft.Container:
        r = self.calc_result
        t = self.loc.get
        notes = []
        if r.aul:
            notes.append(t("calc.aul").format(old=r.base_from, new=r.base))
        if r.radd_applied:
            notes.append(t("calc.radd"))
        if r.asabah_keys:
            names = ", ".join(t(k) for k in r.asabah_keys)
            notes.append(t("calc.asabah").format(names=names))
        if r.unassigned is not None:
            notes.append(t("calc.unassigned"))
        if not notes:
            return _inset(ft.Column([], spacing=0))
        return _inset(
            ft.Column([ft.Text("\n".join(f"• {n}" for n in notes), size=12, italic=True)], spacing=0)
        )

    def _empty_tree_card(self) -> ft.Card:
        t = self.loc.get
        return ft.Card(content=ft.Container(
            ft.Column([
                ft.Text(t("calc.tree"), weight=ft.FontWeight.BOLD, size=15),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                _empty_hint(t),
            ], spacing=10),
            padding=16,
            expand=True,
        ))

    def _build_details(self, r) -> ft.Container:
        t = self.loc.get
        eq = _equivalence_lines(r.rows)
        controls = []
        for row, line in zip(r.rows, eq):
            label = t(row.key) + (f" x{row.count}" if row.count > 1 else "")
            controls.append(self._detail_row(label, line))
        if controls and r.unassigned is None:
            lcm = 1
            for row in r.rows:
                lcm = math.lcm(lcm, (row.share * row.count).denominator)
            total_num = sum(row.share * row.count for row in r.rows) * lcm
            controls.append(self._detail_gap())
            controls.append(ft.Text(
                f"{total_num.numerator}/{lcm} = 1",
                size=12,
                weight=ft.FontWeight.BOLD,
            ))
        if r.blocked_reasons:
            if controls:
                controls.append(self._detail_gap())
            controls.append(ft.Text(
                t("calc.blocked") + ":", size=12, weight=ft.FontWeight.BOLD,
            ))
            controls.extend(
                ft.Text(f"{t(k)} - {t(reason)}", size=12)
                for k, reason in r.blocked_reasons.items()
            )
        if self.estate.has_numbers and r.residual != 0 and r.unassigned is None:
            if controls:
                controls.append(self._detail_gap())
            controls.append(ft.Text(
                t("calc.residual").format(amount=format_amount(self.loc, r.residual)), size=12,
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

    @staticmethod
    def _detail_gap() -> ft.Divider:
        return ft.Divider(height=9, color=ft.Colors.OUTLINE_VARIANT)

    @staticmethod
    def _detail_row(label, value):
        """One heir on a row, shares aligned in their own column so the numbers
        line up instead of running together inside a single wrapped blob."""
        return ft.Row([
            ft.Text(label, size=12, expand=4, no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS, tooltip=label),
            ft.Text(value, size=12, expand=3, text_align=ft.TextAlign.RIGHT,
                    no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, tooltip=value),
        ], spacing=8)

    async def _scroll_to_result(self):
        if self._scroll_host is not None:
            await self._scroll_host.scroll_to(scroll_key="result-card", duration=400)

    def _on_calculate(self, e):
        self._collect()
        self._compute()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self._scroll_to_result())
        else:
            loop.create_task(self._scroll_to_result())

    def _form_pane_width(self) -> float:
        """The width the form pane actually gets, mirroring the layout in build().

        Flet resolves `col` against `page.width`, but the heir card lives in the form
        pane, which in two-pane mode is only half the window. Anything that has to
        fit inside a field has to be measured against the pane, not the window."""
        available = (self.page.width or 0) - GUTTER * 3
        if self.two_pane:
            available = (available - GUTTER) / 2
        return available - CARD_PADDING * 2

    def _heir_col(self, need: int) -> int:
        """Span for one heir field, as a plain int.

        This deliberately is not a window-conditional dict like {"sm": 12, "md": 6}.
        That asks Flet for two fields side by side from 768px of *window* upwards, but
        between roughly 992 and 1180 the form pane is only 484-583px wide, so each
        field got 230-280px to hold a 150px label and an entry. They overlapped the
        neighbouring field. Choosing the span from the pane's own width takes the
        window out of the decision entirely.

        `need` is how much one cell has to hold, which differs by row type: a count
        field carries a 150px label plus an entry, a parent row is just a checkbox."""
        cell = (self._form_pane_width() - GUTTER) / 2
        return 6 if cell >= need else 12

    def _heir_section(self, section, keys):
        """One titled block of the heir card. Spouse is a radio group plus the wife
        count; the other sections are paired count fields. Both go through here so
        the sections cannot drift apart."""
        t = self.loc.get
        if section == "spouse":
            # The wife count belongs beside the choice that enables it. It cannot
            # stay in one `wrap=True` row, because a wrapping child greedily takes
            # the full pane width and pushed the dropdown underneath at every size.
            # The pane decides instead: side by side while they fit, underneath when
            # they do not.
            if self._form_pane_width() >= MIN_SPOUSE_INLINE_WIDTH:
                body = [ft.Row([self._spouse, self._wife_count], spacing=12)]
            else:
                body = [self._spouse, self._wife_count]
        else:
            body = [
                ft.ResponsiveRow(
                    [self._heir_field_row(k) for k in pair],
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

    def _heir_field_row(self, key) -> ft.Row:
        t = self.loc.get
        if key in self._parent_checkboxes:
            return ft.Row(
                [self._parent_checkboxes[key]],
                col=self._heir_col(MIN_CHECKBOX_WIDTH),
            )
        field = self._count_fields[key]
        # expand so the entry takes exactly what the label leaves over and can never
        # push out past its own cell
        field.expand = True
        return ft.Row(
            [_label(t(key)), field],
            col=self._heir_col(LABEL_WIDTH + MIN_FIELD_WIDTH),
            spacing=8,
        )

    def build_appbar_action(self) -> ft.IconButton:
        return ft.IconButton(
            key="appbar-calculate",
            icon=ft.Icons.CALCULATE,
            tooltip=self.loc.get("calc.calculate"),
            on_click=self._on_calculate,
        )

    def build(self):
        t = self.loc.get
        self.two_pane = is_two_pane(getattr(self.page, "width", None))
        self._spouse = ft.RadioGroup(
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
            on_change=lambda e: self._sync_wife_count(),
        )
        self._wife_count = ft.Dropdown(
            key="count-wife",
            label=t("wife"),
            options=[ft.DropdownOption(key=str(n), content=ft.Text(str(n))) for n in range(1, 5)],
            value="1",
            width=110,
        )
        self._count_fields = {
            key: _count_field(key, t, show_label=False)
            for _, keys in heirs.HEIR_SECTIONS
            for key in keys
            if key not in ("husband", "wife", "father", "mother")
        }
        self._parent_checkboxes = {
            key: ft.Checkbox(key=key, label=t(key), value=False)
            for key in ("father", "mother")
        }
        self._sync_wife_count()
        self._tf = {
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
                on_change=lambda e, k=k: self._format_estate_field(k),
            )
            for k in ("estate-gross", "estate-funeral", "estate-debts", "estate-wasiat")
        }
        header = ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, key="back-home", tooltip=t("calc.back"), on_click=lambda e: self.back_home and self.back_home()),
            ft.Text(t("calc.title"), size=22, weight=ft.FontWeight.BOLD),
        ])
        estate_card = ft.Card(content=ft.Container(
            ft.Column([
                ft.Text(t("calc.estate"), weight=ft.FontWeight.BOLD, size=15),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Row(list(self._tf.values()), wrap=True),
            ], spacing=16),
            padding=16,
        ))
        heirs_card = ft.Card(content=ft.Container(
            ft.Column([
                ft.Text(t("calc.heirs"), weight=ft.FontWeight.BOLD, size=15),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                *[
                    self._heir_section(section, keys)
                    for section, keys in heirs.HEIR_SECTIONS
                ],
            ], spacing=16),
            padding=16,
        ))
        calc_btn = ft.FilledButton(
            content=t("calc.calculate"),
            key="btn-calculate",
            width=260, height=48,
            on_click=self._on_calculate,
        )
        form_controls = [estate_card, heirs_card, ft.Row([calc_btn], alignment=ft.MainAxisAlignment.CENTER)]
        if self.two_pane:
            form_pane = ft.Column(
                form_controls,
                spacing=14,
                key="col-cards",
                expand=1,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            )
            result_pane = ft.Column(
                [self.result_card],
                spacing=14,
                key="pane-result",
                expand=1,
                scroll=ft.ScrollMode.AUTO,
            )
            panes = ft.Row(
                [form_pane, result_pane],
                spacing=8,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            )
            root_scroll = None
        else:
            form_pane = ft.Column(
                form_controls,
                spacing=14,
                col={"sm": 12, "lg": 6},
                key="col-cards",
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            )
            result_pane = ft.Column(
                [self.result_card],
                spacing=14,
                col={"sm": 12, "lg": 6},
                key="pane-result",
            )
            panes = ft.ResponsiveRow([form_pane, result_pane], run_spacing=8)
            root_scroll = ft.ScrollMode.AUTO
        self._root = ft.Column(
            controls=[header, panes],
            spacing=14,
            scroll=root_scroll,
            expand=True,
        )
        self._scroll_host = result_pane if self.two_pane else self._root
        return self._root


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