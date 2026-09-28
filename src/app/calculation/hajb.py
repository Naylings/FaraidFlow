from .heirs import HEIR_KEYS


def surviving(heirs: dict) -> dict:
    out = {k: heirs.get(k, 0) for k in HEIR_KEYS}
    has_son = out["son"] > 0
    has_daughter = out["daughter"] > 0
    has_father = out["father"] > 0
    has_full_brother = out["brother_full"] > 0

    if has_son or has_father:
        for k in ("brother_full", "sister_full", "brother_consang", "sister_consang"):
            out[k] = 0
    elif has_full_brother:
        out["brother_consang"] = 0
        out["sister_consang"] = 0

    if has_son or has_daughter or has_father:
        out["brother_uterine"] = 0
        out["sister_uterine"] = 0

    return out