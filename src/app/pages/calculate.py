# src/app/pages/calculate.py

import flet as ft

from app.calculation import engine, heirs
from app.calculation import estate as estate_mod
from app.localization.localization import Localization


class CalculationPage:
    def __init__(self, page, localization: Localization, back_home=None):
        self.page = page
        self.loc = localization
        self.back_home = back_home
        self.heirs: dict[str, int] = {}
        self.estate = estate_mod.Estate()
        self.calc_result: engine.Result | None = None
        self.result_card = ft.Column(spacing=12)

    def _num(self, control_key, default_text="0"):
        tf = self._tf[control_key]
        try:
            return max(0, int(tf.value or default_text or "0"))
        except ValueError:
            return 0

    def _count_of(self, field) -> int:
        try:
            return max(0, int(field.value or 0))
        except (TypeError, ValueError):
            return 0

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

    def _build_tree(self) -> ft.Card:
        t = self.loc.get
        branches = []
        for section, keys in heirs.HEIR_SECTIONS:
            present = {k: self.heirs.get(k, 0) for k in keys if self.heirs.get(k, 0) > 0}
            if not present and section != "spouse":
                continue
            chips = ft.Column([
                ft.Chip(label=ft.Text(t(k) + (f" x{c}" if c > 1 else "")), bgcolor=ft.Colors.SURFACE_CONTAINER)
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
            for e in r.errors:
                claims.append(ft.Text(t(e), color=ft.Colors.ERROR))
        if self.estate.debts > 0 and not r.errors:
            claims.append(ft.Text(t("calc.debt_note"), italic=True, size=12))
        if not self.estate.wasiat_ok and not r.errors:
            claims.append(ft.Text(t("calc.wasiat_warn"), color=ft.Colors.AMBER))
        if self.estate.net <= 0:
            if self.estate.unpaid > 0:
                claims.append(ft.Text(t("calc.depleted").format(amount=f"{self.estate.unpaid:,}"), color=ft.Colors.ERROR))
            else:
                claims.append(ft.Text(t("calc.nothing"), color=ft.Colors.ERROR))

        if claims:
            blocks.append(ft.Column(claims, spacing=6))

        if r.rows:
            rows = [
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(t(row.key) + (f"  x{row.count}" if row.count > 1 else ""))),
                    ft.DataCell(ft.Text(_fmt_num(row.share))),
                    ft.DataCell(ft.Text(f"Rp{row.amount:,}" if row.amount is not None else "-")),
                ])
                for row in r.rows
            ]
            blocks.append(
                ft.DataTable(
                    key="result-table",
                    columns=[
                        ft.DataColumn(ft.Text(t("calc.col_heir"))),
                        ft.DataColumn(ft.Text(t("calc.col_share"))),
                        ft.DataColumn(ft.Text(t("calc.col_amount"))),
                    ],
                    rows=rows,
                )
            )
            blocks.append(self._build_breakdown())
            blocks.append(self._build_notes())

        return ft.Column(controls=blocks, spacing=10)

    def _build_breakdown(self) -> ft.Text:
        e = self.estate
        t = self.loc.get
        line = (
            f"{t('calc.gross')} {e.gross:,} - {t('calc.funeral')} {e.funeral:,} - "
            f"{t('calc.debts')} {e.debts:,} - {t('calc.wasiat')} {e.wasiat:,} = "
            f"{t('calc.net')} {e.net:,}"
        )
        if not e.wasiat_ok:
            line += (
                f"  ({t('calc.wasiat_warn')} {t('calc.wasiat_cap')} {e.wasiat_cap:,}"
                f", {t('calc.wasiat_exc')} {e.wasiat_excess:,}; {t('calc.wasiat_consent')})"
            )
        return ft.Text(line, size=12)

    def _build_notes(self) -> ft.Text:
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
        net = self.estate.net
        if net and r.rows:
            total = sum(row.amount for row in r.rows)
            if total != net:
                notes.append(t("calc.rounded"))
        return ft.Text("  ".join(notes), size=12, italic=True) if notes else ft.Text("")

    def build(self):
        t = self.loc.get
        self._spouse = ft.RadioGroup(
            value="none",
            content=ft.Row([
                ft.Radio(value="none", label=t("calc.spouse_none")),
                ft.Radio(value="husband", label=t("husband")),
                ft.Radio(value="wife", label=t("wife"), tooltip=t("wife")),
            ]),
        )
        self._wife_count = _count_dropdown(1, 4, 1, t("wife"))
        self._count_fields = {
            key: _count_dropdown(0, 10, 0, t(key))
            for _, keys in heirs.HEIR_SECTIONS
            for key in keys
            if key not in ("husband", "wife")
        }
        self._tf = {
            k: ft.TextField(key=k, label=t({"estate-gross": "calc.gross", "estate-funeral": "calc.funeral", "estate-debts": "calc.debts", "estate-wasiat": "calc.wasiat"}[k]), value="", width=180)
            for k in ("estate-gross", "estate-funeral", "estate-debts", "estate-wasiat")
        }
        header = ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, tooltip=t("calc.back"), on_click=lambda e: self.back_home and self.back_home()),
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
                        ft.Text(t(section), size=13),
                        *[ft.Row([ft.Text(t(key)), self._count_fields[key]]) for key in keys if key not in ("husband", "wife")],
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
            on_click=lambda e: (self._collect(), self._compute()),
        )
        return ft.Column(
            controls=[
                header,
                ft.ResponsiveRow([
                    ft.Column([estate_card, heirs_card, calc_btn], spacing=14, col={"sm": 12, "lg": 6}),
                    ft.Column([self.result_card], spacing=14, col={"sm": 12, "lg": 6}),
                ], run_spacing=8),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
        )


def _count_dropdown(min_v, max_v, value, label):
    return ft.Dropdown(
        label=label,
        value=str(value),
        options=[ft.dropdown.Option(str(i)) for i in range(min_v, max_v + 1)],
        width=110,
    )


def _fmt_num(frac) -> str:
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"