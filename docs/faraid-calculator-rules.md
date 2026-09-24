# FaraidFlow Calculator — Engine Rules (scope B)

Working rules for the inheritance engine. Scope B = core nuclear family (spouse, children, parents) + siblings (kandung / seayah / seibu). Appendix to the calculation design spec; verify before the spec is frozen.

## 1. Estate pipeline (applied before any heir share)

```
Net distributable = Gross assets − funeral costs − total debts − valid wasiat
```

- Wasiat is capped at **1/3** of (gross − funeral − debts). If wasiat > 1/3 → **warning**, not a hard error (fiqh leaves excess to heirs' consent).
- If debts > 0 (even Rp1) → app shows the info note: *"Utang bukan warisan — utang melekat pada harta peninggalan dan diselesaikan sebelum sisa dibagikan; dan dapat ditunaikan/ditagih dalam keadaan tertentu."* (per doc §5.2)
- If the net is ≤ 0 → **error**: "nothing to distribute."
- Heir shares are fractions of the **net**, not of gross.

## 2. Heir types covered (scope B)

| Key | Label (EN/ID) | Count |
|---|---|---|
| `husband` | Husband / Suami | 0–1 |
| `wife` | Wife (wives) / Istri | 0–4, share equal |
| `son` | Son / Anak laki-laki | 0+ |
| `daughter` | Daughter / Anak perempuan | 0+ |
| `father` | Father / Ayah | 0–1 |
| `mother` | Mother / Ibu | 0–1 |
| `brother_full` | Full brother / Saudara kandung laki-laki | 0+ |
| `sister_full` | Full sister / Saudara kandung perempuan | 0+ |
| `brother_consang` | Paternal (seayah) brother / Saudara seayah laki-laki | 0+ |
| `sister_consang` | Paternal (seayah) sister / Saudara seayah perempuan | 0+ |
| `brother_uterine` | Uterine (seibu) brother / Saudara seibu laki-laki | 0+ |
| `sister_uterine` | Uterine (seibu) sister / Saudara seibu perempuan | 0+ |

Uterine siblings share one undivided pool, split equally regardless of gender, and are never `'asabah`.

## 3. Fixed shares (`ashab al-furudh`)

| Heir | Share | Condition |
|---|---|---|
| Husband | **1/2** | no children alive |
| Husband | **1/4** | children alive |
| Wife/wives (equal split) | **1/4** | no children alive |
| Wife/wives (equal split) | **1/8** | children alive |
| Single daughter | **1/2** | no son alive |
| 2+ daughters | **2/3** shared | no son alive |
| Father | **1/6** | a son is alive (see §5 for his residue role) |
| Mother | **1/6** | children alive, **or** 2+ siblings present (any mix, even if they end up blocked) |
| Mother | **1/3** | no children and fewer than 2 siblings present (classical form) |
| Single full sister | **1/2** | no full brother, no son, no father alive (daughters allowed) |
| 2+ full sisters | **2/3** shared | no full brother, no son, no father alive (daughters allowed) |
| Single consanguine sister | **1/2** | no consanguine brother, no full brother, no son, no father alive (daughters allowed) |
| 2+ consanguine sisters | **2/3** shared | same conditions as single |
| Uterine sibling(s), single | **1/6** (pool) | no child (son or daughter), no father alive |
| Uterine siblings, 2+ | **1/3** (pool, equal) | no child (son or daughter), no father alive |

Consanguine sister details: with exactly **one full sister** and no brother, she tops the share up to **1/6** (full sister 1/2 + her 1/6 = the 2/3 cap); with **2+ full sisters** she is **excluded** (the cap is already filled).

> **Note — "children"** throughout this document means **direct son or daughter only**. Grandchildren are out of scope B, though classical faraidh includes a son's descendants in the same role.

### Mother's 1/3 — the two 'Umar cases (needs your confirmation)

When the only heirs are **spouse + father + mother** (no children), classical faraidh gives the mother **1/3 of the remainder**, not 1/3 of the whole estate:

- Husband + parents: husband 1/2, mother = 1/3 of remaining 1/2 = **1/6**, father gets 1/3.
- Wife + parents: wife 1/4, mother = 1/3 of remaining 3/4 = **1/4**, father gets 1/2.

Some Indonesian/KHI summaries teach mother = 1/3 of the whole estate. **Flagged: which do we implement?** (Recommended: the classical remainder form, since we follow classical core; BAZNAS's own calculator appears to use it.)

## 4. Blocking (`hajb`) — who disappears entirely

Order of application matters. A blocked heir is removed before shares are computed.

| Heir | Totally blocked by |
|---|---|
| Full brother & full sister | son, or father |
| Consanguine brother & sister | son, father, or **full brother** |
| Uterine brother & sister | son, **or daughter**, or father (never blocked by siblings, never `'asabah`) |
| (Mother's 1/3 → 1/6) | children alive, or 2+ siblings present (any mix, even if they end up blocked) |

Consequences visible to users:

- A **full/consanguine sibling** can be a possible heir only when the deceased left **no son and no father** — a daughter does *not* block them (a sister can even become `'asabah` alongside her).
- **Uterine siblings** can appear only when the deceased left **no child at all (son or daughter) and no father**.

## 5. `'Asabah` (residue takers)

Order of precedence (scope B), nearest first:

1. **Son(n)** — always takes all residue; with daughters, pool is split **2:1** (son twice a daughter).
2. **Father** — **1/6 with a son**; **1/6 + residue with daughters only**; **pure residue with no descendants**.
3. **Full brother** — residue (with full sisters, pool 2:1).
4. **Consanguine brother** — residue (with consanguine sisters, pool 2:1).

### Woman-with-daughter rule (`'asabah ma'a al-ghayr`) — needed for correctness

A full or consanguine **sister becomes `'asabah` alongside a daughter** (when no son and no brother). Example: wife (1/8) + 2 daughters (2/3) + full sister: sister takes the residue = **5/24**. Without this rule the sister would be wrongly excluded and the residue misassigned to `radd` or left dangling.

## 6. `'Aul` — shares exceed the estate

If the furudh sum > 1, enlarge the **base** to the sum of numerators (shares scale down proportionally, spouse included).

Example: wife + 2 daughters + mother + father →
1/8 + 2/3 + 1/6 + 1/6 = 3/24 + 16/24 + 4/24 + 4/24 = **27/24 → base 27**.
Shares: wife 3/27, daughters 16/27, mother 4/27, father 4/27.
The app shows the base (ashlul masalah) and flags that `'aul` raised it 24 → 27.

## 7. `Radd` — residue with no `'asabah`

When furudh < 1 and there is no `'asabah`, return the residue to the fixed heirs **proportionally to their shares, excluding the spouse**.

Example: mother (1/6) + single daughter (1/2) → furudh = 2/3, residue 1/3.
Weights daughter:mother = 3:1 → after radd: daughter **3/4**, mother **1/4**.

Edge (flagged): **sole heir is a wife** → she gets 1/4 and 3/4 residue has no radd recipient (spouse excluded). App will show this residue as "unassigned residue — needs legal/fiqh guidance," not silently give it away.

## 8. Amounts & rounding

- Engine computes exact `fractions.Fraction` shares; the UI renders per-heir amounts as `estate × share` rounded to the nearest Rupiah.
- If rounding leaves a 1–2 Rupiah gap, the app shows a small "rounded" note (academic aid, not a formal settlement).
- All estate fields are ≥ 0 integers; amounts formatted as Indonesian Rupiah (`Rp450.000.000`).

## 9. Behavior rules for the page

- No heirs selected → **error**, no calculation.
- Estate fields left blank → treated as 0 (so "fractions only" still works), but if all are 0 the amount column shows `—`.
- Wasiat > 1/3 net → warning shown, calculation still runs on the entered wasiat.
- Debt note (item 1) shown whenever debts > 0.
- Results footer: distributable net, base (ashlul masalah), `'aul`/`radd` note, `'asabah` recipient note.

## 10. Verification fixtures (must all pass)

| # | Heirs | Shares expected |
|---|---|---|
| 1 | husband + father + mother (no children) | 1/2, 1/6, m 1/6 (1/3 of remainder), father rest 1/3 |
| 2 | wife + father + mother | wife 1/4, m 1/4 (1/3 of 3/4), father 1/2 |
| 3 | husband + mother (no children, no father) | husband 1/2, mother 1/3, residue 1/6 → no asabah → radd excludes spouse → mother takes ridded 1/6 → **husband 1/2, mother 1/2** |
| 4 | wife + 2 daughters + mother + father | **'aul** base 24→27 (wife 3/27, 2d 16/27, m 4/27, f 4/27) |
| 5 | son + 2 daughters (no parents) | residue all, son twice each daughter → 1/2, 1/4, 1/4 |
| 6 | single daughter + father | daughter 1/2, father 1/6 + residue = 1/2 |
| 7 | wife + 2 daughters + full sister | wife 1/8, daughters 2/3, sister **5/24** (asabah ma'a al-ghayr) |
| 8 | wife + 2 full sisters (kalalah) | wife 1/4, sisters 2/3, residue 1/12 → radd (spouse excluded) → wife 1/4, each sister 3/8 |
| 9 | mother + single daughter | radd → daughter 3/4, mother 1/4 |
| 10 | wife only | wife 1/4; residue 3/4 flagged unassigned |
| 11 | brother_full (alone) | 100% via asabah |
| 12 | son + father + wife + mother | wife 1/8, mother 1/6, father 1/6, son residue = 13/24 |
| 13 | 2 uterine brothers (kalalah) | 1/3 pool, split equal; no asabah → radd (both are furudh, no spouse to exclude) → each brother **1/2** |
| 14 | full sister + consanguine sister (kalalah) | full 1/2, consang tops up to 1/6, no asabah → radd → **full 3/4, consang 1/4** |
| 15 | 2 full sisters + consanguine sister (kalalah) | consang excluded, full sisters 2/3, residue 1/3 → radd → each full sister **1/2** |
| 16 | wife + 2 daughters + father | wife 1/8, daughters 2/3, father 1/6 + residue 1/24 = **5/24** |

Fixtures will be cross-checked against the BAZNAS calculator (menara.baznas.go.id/kalkulator_waris) where the case shape matches, and any mismatch is resolved before the spec freezes.

## 11. Explicitly OUT of scope B

- Grandchildren, grandparents (except f/m), `dhawu al-arham`
- Penyelesaian hutang/aset detail, harta bersama, ahli waris pengganti (KHI), anak angkat, perbedaan mazhab
- Jurisdiction toggle (single classical core; app always notes "verify with an authorised person")
- Wasiat recipient logic (only the 1/3 cap is modeled)