HEIR_KEYS = [
    "husband", "wife", "son", "daughter", "father", "mother",
    "brother_full", "sister_full", "brother_consang", "sister_consang",
    "brother_uterine", "sister_uterine",
]

HEIR_SECTIONS = [
    ("spouse", ["husband", "wife"]),
    ("children", ["son", "daughter"]),
    ("parents", ["father", "mother"]),
    (
        "siblings",
        [
            "brother_full", "sister_full", "brother_consang",
            "sister_consang", "brother_uterine", "sister_uterine",
        ],
    ),
]

_SIBLING_KEYS = [
    "brother_full", "sister_full", "brother_consang", "sister_consang",
    "brother_uterine", "sister_uterine",
]


def normalize(raw: dict) -> dict:
    heirs = {k: max(0, int(raw.get(k, 0) or 0)) for k in HEIR_KEYS}
    heirs["husband"] = min(heirs["husband"], 1)
    return heirs


def errors(raw: dict) -> list:
    errs = []
    counts = {k: max(0, int(raw.get(k, 0) or 0)) for k in HEIR_KEYS}
    valid = {k: v for k, v in counts.items() if v > 0}
    if not valid:
        errs.append("calc.errors.no_heirs")
    if counts["husband"] and counts["wife"]:
        errs.append("calc.errors.spouse_both")
    return errs