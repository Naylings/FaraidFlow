# src/app/pages/calculate.py

import asyncio

import flet as ft

from app.calculation import estate as estate_mod
from app.calculation.state import CalculationState
from app.localization.localization import Localization
from app.ui.calculate.claims import build_claims
from app.ui.calculate.details import build_details, build_notes
from app.ui.calculate.estate_form import build_estate_card
from app.ui.calculate.heirs_form import build_heirs_card
from app.ui.calculate.shared import (
    CARD_PADDING,
    GUTTER,
    LABEL_WIDTH,
    MIN_CHECKBOX_WIDTH,
    MIN_FIELD_WIDTH,
    MIN_SPOUSE_INLINE_WIDTH,
    _fmt_int,
    _parse_int,
    format_amount,
    is_two_pane,
)
from app.ui.calculate.table import build_breakdown, build_result_table
from app.ui.calculate.tree import build_empty_tree_card, build_tree

# Layout thresholds live in `app.ui.calculate.shared`, but the suite reads them
# through this page, so they stay re-exported here and keep resolving.
__all__ = [
    "LABEL_WIDTH",
    "MIN_CHECKBOX_WIDTH",
    "MIN_FIELD_WIDTH",
    "MIN_SPOUSE_INLINE_WIDTH",
]


class CalculationPage:
    def __init__(self, page, localization: Localization, back_home=None):
        self.page = page
        self.loc = localization
        self.back_home = back_home
        self.state = CalculationState()
        self.result_card = ft.Column(spacing=12, key=ft.ScrollKey("result-card"))
        self._parent_checkboxes: dict[str, ft.Checkbox] = {}
        self._root = None
        self.two_pane = is_two_pane(getattr(page, "width", None))
        self._scroll_host = None

    @property
    def heirs(self) -> dict[str, int]:
        return self.state.heirs

    @heirs.setter
    def heirs(self, value: dict[str, int]) -> None:
        self.state.heirs = value

    @property
    def estate(self):
        return self.state.estate

    @estate.setter
    def estate(self, value) -> None:
        self.state.estate = value

    @property
    def calc_result(self):
        return self.state.result

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
        self.state.collect(self._slot_from_inputs(), self._estate_from_inputs())

    def _compute(self):
        self.state.compute()
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

    def _amount(self, value) -> str:
        return format_amount(self.loc, value)

    def _build_result(self) -> ft.Column:
        r = self.calc_result
        t = self.loc.get
        blocks = []

        if not r.errors and self.heirs:
            blocked = getattr(self.calc_result, "blocked_reasons", {}) or {}
            blocks.append(build_tree(t, self.heirs, blocked))
        else:
            blocks.append(build_empty_tree_card(t))

        claims = build_claims(t, r, self.heirs, self.estate, self._amount)
        if claims is not None:
            blocks.append(claims)

        blocks.append(build_result_table(t, r.rows, self._amount))
        if r.rows:
            blocks.append(build_breakdown(t, self.estate, self._amount))
            blocks.append(build_notes(t, self.calc_result))
        blocks.append(build_details(t, self.calc_result, self.estate, self._amount))

        return ft.Column(
            controls=blocks,
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

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
        estate_card, self._tf = build_estate_card(t, self._format_estate_field)
        heirs_card, refs = build_heirs_card(
            t,
            on_spouse_change=self._sync_wife_count,
            col_for=self._heir_col,
            pane_width=self._form_pane_width(),
        )
        self._spouse = refs["spouse"]
        self._wife_count = refs["wife_count"]
        self._count_fields = refs["count_fields"]
        self._parent_checkboxes = refs["parent_checkboxes"]
        self._sync_wife_count()
        header = ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, key="back-home", tooltip=t("calc.back"), on_click=lambda e: self.back_home and self.back_home()),
            ft.Text(t("calc.title"), size=22, weight=ft.FontWeight.BOLD),
        ])
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