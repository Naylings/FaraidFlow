# Quick-fix changes — 2026-09-25

Three small UX fixes to the Calculate page, applied after the heirs-form/decimal-results
rework. No spec/plan was created for these (explicitly waived by the user). This file
documents exactly what changed so it can be reverted if anything looks wrong.

Base commit before these changes: `6868763` (Task 11).
All changes are confined to `src/app/pages/calculate.py`.

---

## 1. Estate fields default to `0`

**Change:** the four estate number inputs (`gross`, `funeral`, `debts`, `wasiat`) now
initialize with `value="0"` instead of `value=""`.

**Why:** the live thousands-comma formatter meant a field could not be emptied back to
blank once it held a value. Defaulting to `0` gives a stable starting value.

**Safety:** unchanged behavior. `Estate.has_numbers` is `gross > 0`, so a gross of `0`
still means "no numbers entered" and the engine still runs in pure-fraction mode. The
`0` default does NOT change any calculation path.

**Revert:** change `value="0"` back to `value=""` in the `self._tf` dict (~line 333).

---

## 2. Removed duplicate label on sibling/child count inputs

**Change:** the son/daughter/brother/sister count `TextField`s no longer carry their own
floating `label` (these already have a text label rendered beside them in the heirs
card). The wife count field keeps its label because it has no beside text.

**Why:** the label was shown twice — once beside the input and once inside/on it.

**Safety:** display-only. Count parsing (`_count_of`) and heir normalization are
untouched. Wife count and parent checkboxes are unchanged.

**Revert:** in the `self._count_fields` dict (~line 318) drop `show_label=False`; or
restore the `label=t(key)` in `_count_field` (~line 404).

---

## 3. Auto-scroll to result after Calculate

**Change:** the Calculate button now uses an `_on_calculate` handler. It collects
inputs, computes, then smoothly scrolls the page down to the result card (400ms
animation). The result `Column` was given `key="result-card"`, and the page's scrollable
root `Column` is stored as `self._root` so it can be scrolled.

**Why:** the result is far down the page; after tapping Calculate the user had to scroll
manually to see it.

**Safety:** compute logic is unchanged and still runs synchronously. The scroll is
fire-and-forget (scheduled on the running event loop), so it can never block or break
the result. If a running loop is unavailable it falls back to `asyncio.run`.

**Revert:** set the button `on_click` back to
`lambda e: (self._collect(), self._compute())` and remove `_on_calculate` /
`_scroll_to_result` / the `self._root` bookkeeping. Keep or drop the `key="result-card"`
and the `show_label` / default-`0` bits independently.

---

## Untracked / stray files
- `main.py` (repo root, content was the single character `f`) was DELETED. It was
  accidental and untracked; it is not part of the app (`src/main.py` is the real entry
  point). Recoverable from nothing — it held no real content.
- `docs/hukum_waris_islam_indonesia_baznas_dan_makkah.md` — a research/reference doc.
  Left UNTRACKED and NOT pushed, at the user's request. It is intentionally not part of
  this feature.
