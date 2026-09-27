# src/app/pages/calculate.py

import asyncio
import math
from decimal import Decimal

import flet as ft

from app.calculation import engine, heirs
from app.calculation import estate as estate_mod
from app.localization.localization import Localization


def _fmt_int(n: int) -> str:
    return f"{n:,}"


def _parse_int(text: str) -> int:
    try:
        return int("".join(ch for ch in (text or "") if ch.isdigit()) or "0")
    except ValueError:
        return 0


def _money(value: Decimal, t) -> str:
    if value is None:
        return "-"
    digits = f"{value:,.2f}"
    return (
        t("money.prefix")
        + digits.replace(".", "\u0000").replace(",", t("money.thousands_sep")).replace("\u0000", t("money.decimal_sep"))
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


LABEL_WIDTH = 150


def _label(text: str) -> ft.Text:
    return ft.Text(
        text,
        width=LABEL_WIDTH,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS,
    )


def _pairs(keys):
    return [tuple(keys[i:i + 2]) for i in range(0, len(keys), 2)]


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
            if not present and section != "spouse":
                continue
            chips = ft.Column([
                ft.Chip(
                    label=ft.Text(t(k) + (f" x{c}" if c > 1 else "")),
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    disabled=k in blocked,
                    tooltip=t("calc.blocked_tip").format(reason=t(blocked[k])) if k in blocked else None,
                )
                for k, c in present.items()
            ], spacing=4)
            branches.append(ft.Column(
                [ft.Text(t(f"calc.{section}"), weight=ft.FontWeight.BOLD, size=12), chips],
                spacing=4,
                col={"sm": 12, "md": 6, "lg": 3},
            ))
        root = ft.Chip(label=ft.Text(t("calc.deceased")), bgcolor=ft.Colors.PRIMARY_CONTAINER)
        return ft.Card(content=ft.Container(
            ft.Column([root, ft.ResponsiveRow(branches, run_spacing=8)], spacing=10),
            padding=16,
        ))

    def _build_result(self) -> ft.Column:
        r = self.calc_result
        t = self.loc.get
        blocks = []

        if not r.errors and self.heirs:
            blocks.append(self._build_tree())

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
                    t("calc.depleted").format(amount=_money(Decimal(self.estate.unpaid), t)),
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

            def _cell(value, weight, bold=False, numeric=False):
                return ft.Text(
                    value,
                    size=12,
                    weight=ft.FontWeight.BOLD if bold else None,
                    expand=weight,
                    text_align=ft.TextAlign.RIGHT if numeric else ft.TextAlign.LEFT,
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                )

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
                    cells.append(_cell(_money(row.each, t2), weights[2][1], numeric=True))
                cells.append(
                    _cell(
                        _money(row.amount, t2) if row.amount is not None else "-",
                        weights[-1][1],
                        numeric=True,
                    )
                )
                table_rows.append(ft.Row(cells, spacing=8))
            blocks.append(ft.Column(table_rows, key="result-table", spacing=6))
            blocks.append(self._build_breakdown())
            blocks.append(self._build_notes())
            blocks.append(self._build_details(r))

        return ft.Column(controls=blocks, spacing=10)

    def _build_breakdown(self) -> ft.Column:
        e = self.estate
        t = self.loc.get
        line = (
            f"{t('calc.gross')} {_money(Decimal(e.gross), t)} - "
            f"{t('calc.funeral')} {_money(Decimal(e.funeral), t)} - "
            f"{t('calc.debts')} {_money(Decimal(e.debts), t)} - "
            f"{t('calc.wasiat')} {_money(Decimal(e.wasiat), t)} = "
            f"{t('calc.net')} {_money(Decimal(e.net), t)}"
        )
        rows = [ft.Text(line, size=12)]
        if not e.wasiat_ok:
            rows.append(ft.Text(
                f"{t('calc.wasiat_warn')} {t('calc.wasiat_cap')} {_money(Decimal(e.wasiat_cap), t)}"
                f", {t('calc.wasiat_exc')} {_money(Decimal(e.wasiat_excess), t)}"
                f"; {t('calc.wasiat_consent')}",
                size=12,
                italic=True,
            ))
        return ft.Column(rows, spacing=4)

    def _build_notes(self) -> ft.Column:
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
            return ft.Column([], spacing=0)
        return ft.Column([ft.Text("\n".join(f"• {n}" for n in notes), size=12, italic=True)], spacing=0)

    def _build_details(self, r) -> ft.ExpansionTile:
        t = self.loc.get
        lines = []
        eq = _equivalence_lines(r.rows)
        if eq:
            for row, line in zip(r.rows, eq):
                label = t(row.key) + (f" x{row.count}" if row.count > 1 else "")
                lines.append(f"{label}: {line}")
            if r.unassigned is None:
                lcm = 1
                for row in r.rows:
                    lcm = math.lcm(lcm, (row.share * row.count).denominator)
                total_num = sum(row.share * row.count for row in r.rows) * lcm
                lines.append(f"{total_num.numerator}/{lcm} = 1")
        if r.blocked_reasons:
            lines.append(t("calc.blocked") + ":")
            lines.extend(f"• {t(k)} — {t(reason)}" for k, reason in r.blocked_reasons.items())
        if self.estate.has_numbers and r.residual != 0 and r.unassigned is None:
            lines.append(t("calc.residual").format(amount=_money(r.residual, t)))
        return ft.ExpansionTile(
            key="calc-details",
            title=ft.Text(t("calc.details")),
            controls=[ft.Text("\n".join(lines), size=12)] if lines else [],
            expanded=False,
        )

    async def _scroll_to_result(self):
        if self._root is not None:
            await self._root.scroll_to(scroll_key="result-card", duration=400)

    def _on_calculate(self, e):
        self._collect()
        self._compute()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self._scroll_to_result())
        else:
            loop.create_task(self._scroll_to_result())

    def _heir_field_row(self, key) -> ft.Row:
        t = self.loc.get
        if key in self._parent_checkboxes:
            return ft.Row([self._parent_checkboxes[key]], col={"sm": 12, "md": 6})
        return ft.Row([_label(t(key)), self._count_fields[key]], col={"sm": 12, "md": 6})

    def build_appbar_action(self) -> ft.IconButton:
        return ft.IconButton(
            key="appbar-calculate",
            icon=ft.Icons.CALCULATE,
            tooltip=self.loc.get("calc.calculate"),
            on_click=self._on_calculate,
        )

    def build(self):
        t = self.loc.get
        self._spouse = ft.RadioGroup(
            value="none",
            content=ft.Row([
                ft.Radio(value="none", label=t("calc.spouse_none")),
                ft.Radio(value="husband", label=t("husband")),
                ft.Radio(value="wife", label=t("wife"), tooltip=t("wife")),
            ]),
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
                ft.Text(t("calc.estate"), weight=ft.FontWeight.BOLD),
                ft.Row(list(self._tf.values()), wrap=True),
            ]),
            padding=16,
        ))
        heirs_card = ft.Card(content=ft.Container(
            ft.Column([
                ft.Text(t("calc.heirs"), weight=ft.FontWeight.BOLD),
                ft.Text(t("calc.spouse"), size=13),
                self._spouse,
                self._wife_count,
                *[
                    ft.Column([
                        ft.Text(t(f"calc.{section}"), size=13),
                        *[
                            ft.ResponsiveRow(
                                [self._heir_field_row(k) for k in pair],
                                spacing=8,
                                run_spacing=8,
                            )
                            for pair in _pairs(keys)
                        ],
                    ])
                    for section, keys in heirs.HEIR_SECTIONS
                    if section in ("children", "parents", "siblings")
                ],
            ]),
            padding=16,
        ))
        calc_btn = ft.FilledButton(
            content=t("calc.calculate"),
            key="btn-calculate",
            width=260, height=48,
            on_click=self._on_calculate,
        )
        self._root = ft.Column(
            controls=[
                header,
                ft.ResponsiveRow([
                    ft.Column([estate_card, heirs_card, ft.Row([calc_btn], alignment=ft.MainAxisAlignment.CENTER)], spacing=14, col={"sm": 12, "lg": 6}, key="col-cards", horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                    ft.Column([self.result_card], spacing=14, col={"sm": 12, "lg": 6}),
                ], run_spacing=8),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        return self._root


def _count_field(key, t, show_label=True):
    return ft.TextField(
        key=f"count-{key}",
        label=t(key) if show_label else None,
        value="0",
        width=110,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.NumbersOnlyInputFilter(),
    )


def _fmt_num(frac) -> str:
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"