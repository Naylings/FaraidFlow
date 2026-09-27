# Quick-fix changes — 2026-09-25

A batch of UX + correctness fixes to the Calculate page, applied after the
heirs-form/decimal-results rework. No spec/plan was created for these (explicitly
waived by the user). This file documents exactly what changed so it can be reverted if
anything looks wrong.

Base commit before the first round: `6868763` (Task 11).
Round 1 (items 1–3) is commit `f79ef48`; round 2 (items 4–6) is the follow-up commit.

---

## Round 1

All changes are confined to `src/app/pages/calculate.py`.

### 1. Estate fields default to `0`

**Change:** the four estate number inputs (`gross`, `funeral`, `debts`, `wasiat`) now
initialize with `value="0"` instead of `value=""`.

**Why:** the live thousands-comma formatter meant a field could not be emptied back to
blank once it held a value. Defaulting to `0` gives a stable starting value.

**Safety:** unchanged behavior. `Estate.has_numbers` is `gross > 0`, so a gross of `0`
still means "no numbers entered" and the engine still runs in pure-fraction mode. The
`0` default does NOT change any calculation path.

**Revert:** change `value="0"` back to `value=""` in the `self._tf` dict (~line 333).

---

### 2. Removed duplicate label on sibling/child count inputs

**Change:** the son/daughter/brother/sister count `TextField`s no longer carry their own
floating `label` (these already have a text label rendered beside them in the heirs
card). The wife count field keeps its label because it has no beside text.

**Why:** the label was shown twice — once beside the input and once inside/on it.

**Safety:** display-only. Count parsing (`_count_of`) and heir normalization are
untouched. Wife count and parent checkboxes are unchanged.

**Revert:** in the `self._count_fields` dict (~line 318) drop `show_label=False`; or
restore the `label=t(key)` in `_count_field` (~line 404).

---

### 3. Auto-scroll to result after Calculate

**File:** `src/app/pages/calculate.py`
**Change:** the result `Column` key was changed from a plain string to a scroll key:
`key="result-card"` became `key=ft.ScrollKey("result-card")`.

**Status: THE ROOT CAUSE.** Flet 1.0 has a breaking change where `scroll_to(scroll_key=...)`
only matches controls whose key is wrapped in `ft.ScrollKey(...)` — a plain string key is
**silently ignored**, so the page never moved. This was the actual reason auto-scroll did
not work in the real app (previously misdiagnosed as an animation/timing issue).

Confirmed against:
- flet issue [#5238](https://github.com/flet-dev/flet/issues/5238) — "`scroll_to()`:
  `key` renamed to `scroll_key`; in control key should be `key=ft.ScrollKey()`"
- flet issue [#5638](https://github.com/flet-dev/flet/issues/5638) — "`scroll_to` not
  work"; the fix is to use `ft.ScrollKey`.
- The installed flet 1.0.1 source: `scrollable_control.scroll_to()` documents that
  `auto_scroll` must be `False` (it already is) and accepts a `scroll_key`.
  `str(ft.ScrollKey("result-card")) == "result-card"`, so the existing string lookup in
  `_scroll_to_result` still matches.

**Not included (deferred, optional robustness):**
- Switching the raw `asyncio.get_running_loop()` / `asyncio.run()` scheduling in
  `_on_calculate` to Flet's own `page.run_task()`.
- Awaiting `page.update()` before scrolling, in case the client has not yet laid out the
  freshly rebuilt result card.

Neither was the cause of the failure; they are cleanups only. If the scroll still does
not behave in the real app after this change, the `page.update()` ordering is the next
thing to try.

**Revert:** set `key=ft.ScrollKey("result-card")` back to `key="result-card"` on
`self.result_card` (~line 57).

---

## Round 2 — result table layout, details readability, residual rounding

Base: commit `f79ef48`.

### 4. Result table columns expand to fill the width

**File:** `src/app/pages/calculate.py`
**Change:** each `ft.DataColumn` now sets `expand` (Heir=2, Share=1, Each=2, Total=2).

**Why:** when the Each column is conditionally hidden (only shown when some heir group
has `count > 1`), the remaining columns did not stretch, leaving a large empty gap on
the right side of the table. The empty space was the visible symptom, not a missing
column.

**Safety:** display-only. No calculation or data change.

**Revert:** remove the `expand=N` arguments from the four `ft.DataColumn(...)` calls in
`_build_result`.

---

### 5. Calculation details are one item per line, with heir names

**File:** `src/app/pages/calculate.py`
**Change:** `_build_details` no longer joins the share-equivalence lines with triple
spaces on a single line. Each equivalence line is now on its own line and prefixed with
the heir name and count (e.g. `Son x3: 3/4 = 6/8`). Blocked reasons are listed as
bulleted lines under a `Blocked:` heading. The notes (`_build_notes`) and the wasiat
warning (in `_build_breakdown`) were likewise changed to render one note per line
instead of cramming them together with double spaces.

**Why:** the old single-line, triple-space-separated rendering was hard to read,
especially on narrow layouts.

**Safety:** display-only. The underlying `_equivalence_lines()` helper and all numeric
output are unchanged; the existing tests assert that helper's return value and still
pass.

**Revert:** revert the rendering changes in `_build_details` / `_build_notes` /
`_build_breakdown` only; the arithmetic is untouched.

---

### 6. Residual can no longer be negative (money rounding fix)

**File:** `src/app/calculation/engine.py`
**Change:** two-part fix to the per-person rounding so the leftover `residual` is never
negative and the `Total` column always sums exactly to the net estate:
  1. Each group's `amount` (its share of the net) is quantized independently, then a
     whole-cent `drift` (`net - sum(amounts)`) is added to the largest group so the
     group totals always reconcile to the net exactly.
  2. The per-person `each` is quantized with `ROUND_FLOOR` (not the default
     `ROUND_HALF_EVEN`), so `each * count` never exceeds the group's `amount`.

**Why:** with the old half-even rounding, `each` could round *up*, making
`each * count > amount` and pushing the residual negative (e.g. `son x3` on a net of 5
gave `each=1.67`, `1.67*3=5.01`, residual `-0.01`; two such groups gave `-0.02`). A
fuzz run over ~40k random heir/estate combinations found 71 negative-residual cases
before the fix and 0 after. Flooring `each` guarantees
`residual = net - sum(each*count) >= net - sum(amount) = 0`.

**Safety:** totals are unchanged; only the sub-cent distribution remainder is
reallocated. A case with a genuine remainder (e.g. 3 full brothers splitting 100) still
shows a **positive** `0.01` residual, matching the existing test
`test_residual_nonzero_when_head_split_leaves_cents`. All 110 tests pass.

**Revert:** in the residual block of `engine.resolve`, drop the `drift`-reconciliation
loop and change the `each` quantization back to `.quantize(_QUANT)`. (Note: this
reintroduces the negative-residual bug.)

---

## Round 3 — wife count constrained to a 1–4 dropdown

Base: commit `ac3d20c`.

### 7. Wife count is a dropdown limited to 1–4

**File:** `src/app/pages/calculate.py`
**Change:** the wife count control was changed from a free-text `TextField` to a
non-editable `ft.Dropdown` with exactly four options: `1`, `2`, `3`, `4`. It defaults
to `1` and is still disabled unless the spouse radio is set to "wife".

**Why:** the wife count used to be a free number field, so it could be set to `0`, left
blank, or set to an arbitrary value. That was inconsistent with how the engine actually
behaves — selecting a wife means *at least one* wife — and it conflicted with the
Islamic-law convention of at most four wives. A dropdown makes the valid range explicit
and physically prevents invalid entry at the UI level.

**Scope note:** the wife count dropdown is a **UI-level** constraint only. The engine
still has no hard cap on the wife count (the `min(..., 4)` clamp in
`heirs.normalize` and the `calc.errors.wife_max` message were removed earlier in commit
`d0becdf` and have **not** been restored). The dropdown is what enforces 1–4 in the UI.

**Safety:**
- `_slot_from_inputs` already wrapped the wife count in `max(1, ...)`, so a blank or `0`
  value still resolves to `1` — the dropdown just makes that state unreachable in
  normal use.
- Language-switch state capture/restore still works: the stored wife value is a plain
  string (`"1"`–`"4"`), and a legacy stored value of `""`/`"0"` falls back to `1`
  through the existing `max(1, ...)` guard. Covered by a regression test.
- The son/daughter/brother/sister count fields are **unchanged**. For those, `0` and
  blank legitimately mean "none" and that behavior is intentional.

**Tests added** (`tests/test_calculate_page.py`):
- `test_result_card_uses_scroll_key_so_scroll_to_can_find_it`
- `test_wife_count_is_a_dropdown_limited_to_one_through_four`
- `test_wife_count_dropdown_feeds_slot_and_defaults_to_one`
- `test_wife_count_empty_or_zero_falls_back_to_one`

**Revert:** replace the `ft.Dropdown(...)` assigned to `self._wife_count` in `build()`
with `self._wife_count = _count_field("wife", t)`.

---

## Round 4 — result table fills its container width

Base: commit `a1c5818`.

### 8. Result table rebuilt from Rows so it actually fills the width

**Files:** `src/app/pages/calculate.py`, `tests/test_calculate_page.py`
**Change:** the result table was converted from `ft.DataTable` to a `ft.Column` of
`ft.Row`s (header row, divider, one row per heir). Every cell is an `ft.Text` with an
`expand` weight, so the row always fills the full width of its container regardless of
how many columns are present. Column weights are Heir=3, Share=2, Each=2, Total=2.

Also included: numeric columns (Share/Each/Total) are right-aligned, the header is bold,
and cells use `no_wrap=True` with `TextOverflow.ELLIPSIS` so a long heir name or a very
large amount degrades to an ellipsis instead of breaking the layout.

**Why — and a correction to an earlier claim:** an earlier round (commit `ac3d20c`)
claimed the "empty space" was fixed by adding `expand` to each `ft.DataColumn`. **That
fix did nothing.** Flet confirms Flutter's built-in `DataTable`/`DataColumn` has no
width or flex property, so columns auto-size to their content and the `expand` value on
a `DataColumn` is silently ignored. `ft.Table` and `FlexColumnWidth` do not exist in
flet 1.0.1, and the `flet-datatable2` extension (which does support per-column widths)
is not installed. Rows with `expand` are the only reliable way to get proportional
column widths with the controls available here.

Source: flet discussion [#6418](https://github.com/flet-dev/flet/discussions/6418)
("Flutter's built-in `DataColumn` has no `width` property, so `ft.DataTable` has nothing
to plumb through. Columns auto-size to content, and that's it.").

**Safety:** the table is display-only — no calculation or data change. The
`key="result-table"` is preserved, so `page.find`-style lookups and the existing
integration tests still work. The header order (Heir, Share, [Each], Total) is
unchanged.

**Tests updated/added** (`tests/test_calculate_page.py`): the three existing table tests
now read cells from the Row structure instead of `DataColumn`/`DataCell`, and two new
tests were added:
- `test_result_table_cells_expand_to_fill_container` — every cell has an `expand` weight
- `test_result_table_expands_with_and_without_each_column` — verifies the 4-column and
  3-column layouts both expand every cell

**Revert:** in `_build_result`, replace the `ft.Column(table_rows, key="result-table", ...)`
block with the previous `ft.DataTable(key="result-table", columns=..., rows=...)`
construction, and restore the three tests to read `table.columns` / `ft.DataCell`.

---

## Round 5 — Share column basis bug (group vs per-person)

Base: commit `7b58aab`.

### 9. Share column showed per-person share while Total showed group total

**File:** `src/app/pages/calculate.py`
**Change:** one line in `_build_result` — the Share cell now renders the **group**
share instead of the per-person share:

    - _cell(_fmt_num(row.share), ...)
    + _cell(_fmt_num(row.share * row.count), ...)

**The bug:** for a row representing several heirs of one type, the table mixed two
different bases in the same row. Example (wife + 2 sons, net 1000):

| Column | Before | Basis |
|---|---|---|
| Share | `7/16` | per person |
| Each | `$437.50` | per person |
| Total | `$875.00` | **whole group** |

So the row was labelled `Son x2` and its Total was 7/8 of the estate, yet the Share
cell said 7/16. The "Calculation details" panel was already correct (it shows
`Son x2: 7/8 = 7/8`), which made the two panels appear to contradict each other.

**After:**

| Column | Value | Basis |
|---|---|---|
| Heir | `Son  x2` | group |
| Share | `7/8` | **group** — matches Total |
| Each | `$437.50` | per person |
| Total | `$875.00` | group |

**Note: the underlying calculation was always correct** and was not changed. Only the
displayed fraction was wrong. The per-person split is still fully visible in the
`Each` column, which is its purpose.

**Safety:** display-only; `row.share` itself is untouched, so the engine, the details
panel, and the tests that assert on `Row.share` are unaffected. Verified with a fuzz
run over ~16,700 random heir/estate combinations: the displayed group shares sum to
exactly 1 in every case.

**Tests added** (`tests/test_calculate_page.py`):
- `test_share_column_shows_group_share_not_per_person_share` — the reported wife +
  2 sons case; asserts the cell reads `7/8` and that `7/16` never appears
- `test_share_column_matches_total_column_basis_for_groups` — 3 sons case

**Revert:** change `_fmt_num(row.share * row.count)` back to `_fmt_num(row.share)` in the
Share cell of `_build_result`.

## Untracked / stray files
- `main.py` (repo root, content was the single character `f`) was DELETED. It was
  accidental and untracked; it is not part of the app (`src/main.py` is the real entry
  point). Recoverable from nothing — it held no real content.
- `docs/hukum_waris_islam_indonesia_baznas_dan_makkah.md` — a research/reference doc.
  Left UNTRACKED and NOT pushed, at the user's request. It is intentionally not part of
  this feature.

---

## Round 6 — Calculate page layout redesign (2026-09-27)

Spec: `docs/superpowers/specs/2026-09-27-calculate-page-layout-design.md`.
Plan: `docs/superpowers/plans/2026-09-27-calculate-page-layout.md`.
Base commit: `842fbf3`. Layout and micro-UX only — no calculation logic changed.

### 10. Heir count fields pre-filled with `0`

**Files:** `src/app/pages/calculate.py`, `tests/test_calculate_page.py`
**Change:** `_count_field()` creates count `TextField`s with `value="0"` instead of
`value=""`. The four estate fields already defaulted to `"0"`, so the form was
internally inconsistent — money fields showed `0`, heir fields directly below them
showed blanks.

**Why:** consistency within one form. Blanks under pre-filled money fields read as an
incomplete or buggy state.

**Safety:** no calculation path changes. `Estate.has_numbers` is `gross > 0`, which is
about the *estate*, not heir counts, so pre-filling counts to `0` does not affect it.
`_count_of()` returns `0` for both `""` and `"0"`, and `_slot_from_inputs()` skips
falsy counts, so the two are indistinguishable downstream. `0` legitimately still means
"this heir type is absent" — that meaning is preserved, not removed. The wife control
is a 1–4 `ft.Dropdown` and still defaults to `"1"`; it is an enum, not a free count.
A form left completely untouched now shows the `calc.errors.no_heirs` state, which is
covered by a new test.

**Tests added:** `test_heir_counts_prefilled_with_zero_like_the_estate_fields`,
`test_untouched_form_with_zero_counts_shows_no_heirs_error`.

**Revert:** change `value="0"` back to `value=""` in `_count_field` (~line 437).

### 11. Heir labels get a fixed 150px column

**Files:** `src/app/pages/calculate.py`, `tests/test_calculate_page.py`
**Change:** heir labels moved from a bare `ft.Text(t(k))` to `_label(t(k))`, a helper
that sets `width=LABEL_WIDTH` (150), `no_wrap=True` and
`overflow=ft.TextOverflow.ELLIPSIS`. New module constant `LABEL_WIDTH = 150`.

**Why:** `ft.Text` with no width sizes to its own content, so every input started at a
different x-position — a visible staircase between a short label ("Son") and a long one
("Paternal brother"). A fixed label column puts every input on one vertical axis.

**Safety:** display-only; no parsing or calculation change. `no_wrap` plus ellipsis
means a label that does not fit 150px truncates instead of pushing its input right. The
longest label in either language (`Anak perempuan`, 14 characters) fits inside 150px at
the default text size, so no truncation is expected — confirmed by hand at the narrowest
supported width in the Round 6 manual pass.

**Tests added:** `test_every_heir_label_sits_in_a_fixed_width_column`.

**Revert:** in `build()`, change `_label(t(k))` back to `ft.Text(t(k))` and delete
`LABEL_WIDTH` / `_label()`. Note Task 12's `_heir_field_row()` also calls `_label()` —
revert that call too.
