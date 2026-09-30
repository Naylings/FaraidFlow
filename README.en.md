<div align="center">

# FaraidFlow

**Islamic inheritance calculator (faraid)**

Bahasa Indonesia · [English](README.en.md)

[![Status: beta](https://img.shields.io/badge/status-beta-orange)](#status)

</div>

---

Calculates how an estate is divided under Islamic inheritance law. Enter the
estate's value and who survived the deceased; the app works out each heir's
share, shows the reasoning, and flags the heirs who are **blocked (hajb)** from
inheriting.

Two languages: **Indonesian** and **English**.

> **This is still a beta.** The figures follow the Sunni faraid rules, but check
> any result with a qualified scholar before relying on it for a real estate.
> This app is not a substitute for legal advice.

## Status

The **Calculate**, **Information**, and **About** screens are all functional and accessible from the home screen.

## Features

**Estate**

- Total value of assets
- Funeral costs
- Debts
- Wasiat (bequest) — capped at **one third**, and the app warns you when the
  amount you entered exceeds that cap

**Heirs**

- Husband / wife / none
- Children
- Parents
- Siblings

Each takes a **count** rather than a name, so a large family is quick to enter.

**Results**

- A share table per heir: the fraction, the amount, and the amount each person
  receives
- An inheritance tree — heirs grouped by branch, with the deceased at the root
- The arithmetic, unfolded: every share converted to a common denominator, the
  total shown as `n/lcm = 1`
- **Blocked heirs (hajb)** — who is excluded and why
- **'Aul** (shares exceeding one) and **radd** (the surplus returned to those
  entitled) are both detected and reported

## How to use

1. Open the app and tap **Calculate**.
2. Fill in the estate figures at the top.
3. Pick a spouse if there is one, then fill in the counts for children, parents
   and siblings.
4. Calculate. The table, tree and breakdown appear below.

Switch languages with the button in the top right.

## How the calculation works

- **Debts are not inherited.** They attach to the estate and are settled before
  anything is shared out. Heirs are not obliged to cover the deceased's debts,
  but they may choose to.
- The rules follow the commonly used Sunni scheme. Where a case is disputed or
  not agreed between schools, the choice this project makes is documented in
  `src/app/calculation/`.

Two things worth knowing, because they **differ from some schools**:

- **Radd is returned to the fixed-share heirs, excluding the spouse.** That
  follows the convention this project uses; other schools return the radd to
  everyone entitled, spouse included.
- If only a **spouse** remains once everyone else has been accounted for, the
  surplus is left unassigned and the app tells you to **seek legal or fiqh
  guidance**. It does not resolve that case automatically.

Contributions on exactly these cases are very welcome — open an issue before
sending a patch.

## Download

The repository is public and every build is produced for free by GitHub
Actions.

| Platform | How |
|---|---|
| **Android** | Download the `.apk` from the [releases page](https://github.com/Naylings/FaraidFlow/releases), open it, and allow **Install unknown apps** for whatever app opened it. |
| **Windows** | Download the `.zip` from the [releases page](https://github.com/Naylings/FaraidFlow/releases), extract it, and run `ahli-waris.exe`. |
| **Web** | Open <https://naylings.github.io/FaraidFlow/> — nothing to install. |

### Android and Windows warnings

The APK and the EXE are **signed with a debug key**, not a release
certificate. That means:

- Android will warn that the file came from an unknown source — expected, choose
  **Install anyway**.
- Windows SmartScreen may say "Windows protected your PC" — choose **More info
  → Run anyway**.

Both are fine to run and to share, but neither can go to Google Play. That
needs a release keystore later.

## Run from source

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Naylings/FaraidFlow.git
cd FaraidFlow
uv sync
uv run flet run
```

The web version:

```bash
uv run flet run --web
```

## Development

```bash
uv sync
uv run pytest          # 146 tests
uv run ruff check src
```

> **Note:** Flet 1.0.1 can only be packaged against Flutter 3.44.8. The Flet
> and Flutter versions are pinned exactly in `pyproject.toml` and
> `.github/workflows/release.yml`. If you change one, change the other.

### Layout

| Path | What lives there |
|---|---|
| `src/app/calculation/` | The engine. Pure Python, no UI, no Flet imports. |
| `src/app/localization/` | Indonesian and English strings. |
| `src/app/pages/` | Screens. |
| `src/app/components/` | Shared widgets. |

The engine does not depend on the UI at all, so the rules can be tested
directly.

## Licence

MIT — see [LICENSE](LICENSE).
