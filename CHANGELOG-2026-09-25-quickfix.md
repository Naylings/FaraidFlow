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

## Untracked / stray files
- `main.py` (repo root, content was the single character `f`) was DELETED. It was
  accidental and untracked; it is not part of the app (`src/main.py` is the real entry
  point). Recoverable from nothing — it held no real content.
- `docs/hukum_waris_islam_indonesia_baznas_dan_makkah.md` — a research/reference doc.
  Left UNTRACKED and NOT pushed, at the user's request. It is intentionally not part of
  this feature.
