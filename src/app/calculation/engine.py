# src/app/calculation/engine.py

import math
from dataclasses import dataclass, field
from decimal import Decimal, getcontext
from fractions import Fraction

from .estate import Estate
from .hajb import surviving
from .heirs import HEIR_KEYS, errors, normalize

getcontext().prec = 28

_QUANT = Decimal("0.01")

F = Fraction

_SPOUSE = {"husband", "wife"}
_SIBLINGS = {
    "brother_full", "sister_full", "brother_consang", "sister_consang",
    "brother_uterine", "sister_uterine",
}


@dataclass
class Row:
    key: str
    count: int
    share: Fraction
    amount: Decimal | None = None
    each: Decimal | None = None


@dataclass
class Result:
    rows: list[Row] = field(default_factory=list)
    aul: bool = False
    base: int = 0
    base_from: int = 0
    radd_applied: bool = False
    asabah_keys: list[str] = field(default_factory=list)
    unassigned: Fraction | None = None
    blocked_keys: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    residual: Decimal = field(default_factory=lambda: Decimal(0))


def _base_and_aul(shares):
    lcm = 1
    for s in shares.values():
        if s > 0:
            lcm = math.lcm(lcm, s.denominator)
    nums = sum((s * lcm).numerator for s in shares.values())
    return lcm, nums


def resolve(raw: dict, estate: Estate | None = None) -> Result:
    errs = errors(raw)
    if errs:
        return Result(errors=errs)

    h = normalize(raw)
    eff = surviving(h)
    shares: dict[str, Fraction] = {}  # GROUP fractions

    children = h["son"] + h["daughter"]
    n_sib = sum(h[k] for k in _SIBLINGS)

    # spouse (group)
    if eff["husband"]:
        shares["husband"] = F(1, 4) if children else F(1, 2)
    if eff["wife"]:
        shares["wife"] = F(1, 8) if children else F(1, 4)

    # daughters furudh (group)
    if eff["son"] == 0 and eff["daughter"]:
        shares["daughter"] = F(1, 2) if eff["daughter"] == 1 else F(2, 3)

    # father furudh
    if eff["father"] and (eff["son"] > 0 or eff["daughter"] > 0):
        shares["father"] = F(1, 6)

    # mother
    if eff["mother"]:
        if children or n_sib >= 2:
            shares["mother"] = F(1, 6)
        else:
            shares["mother"] = F(1, 3)

    # amariyyah (1/3 of the remainder when only spouse + parents remain)
    if (
        children == 0
        and n_sib < 2
        and eff["father"]
        and eff["mother"]
        and (eff["husband"] or eff["wife"])
    ):
        spouse_share = shares.get("husband") or shares.get("wife")
        only_these = {
            k for k, v in eff.items() if v > 0
        } <= ({("husband" if eff["husband"] else "wife"), "father", "mother"})
        if only_these:
            shares["mother"] = (F(1, 1) - spouse_share) * F(1, 3)

    # sisters furudh (no son, no father, NO daughter) — group
    if eff["son"] == 0 and eff["father"] == 0 and eff["daughter"] == 0:
        if eff["brother_full"] == 0 and eff["sister_full"]:
            shares["sister_full"] = (
                F(1, 2) if eff["sister_full"] == 1 else F(2, 3)
            )
        if eff["brother_consang"] == 0 and eff["sister_consang"]:
            fs = eff["sister_full"]
            if fs == 1:
                shares["sister_consang"] = F(1, 6)
            elif fs == 0:
                shares["sister_consang"] = (
                    F(1, 2) if eff["sister_consang"] == 1 else F(2, 3)
                )

    # uterine pool (group split proportional to headcount)
    if (
        eff["son"] == 0
        and eff["daughter"] == 0
        and eff["father"] == 0
        and (eff["brother_uterine"] or eff["sister_uterine"])
    ):
        n_uterine = eff["brother_uterine"] + eff["sister_uterine"]
        pool = F(1, 6) if n_uterine == 1 else F(1, 3)
        if eff["brother_uterine"]:
            shares["brother_uterine"] = (
                pool * eff["brother_uterine"] / n_uterine
            )
        if eff["sister_uterine"]:
            shares["sister_uterine"] = pool * eff["sister_uterine"] / n_uterine

    # base computed from FURUDH shares pre-'aul (pre-radd) — classical asl
    base_from, nums = _base_and_aul(shares)

    asabah_keys: list[str] = []
    radd_applied = False
    unassigned = None

    total = sum(shares.values())
    if total > 1:
        # 'aul: furudh alone exceed the estate
        aul = True
        base = nums
        scale = F(base_from, base)
        shares = {k: s * scale for k, s in shares.items()}
    else:
        aul = False
        base = base_from
        if total < 1:
            residue = F(1, 1) - total
            if eff["son"]:
                asabah_keys = ["son"] + (["daughter"] if eff["daughter"] else [])
                k = residue / (2 * eff["son"] + eff["daughter"])
                shares["son"] = 2 * k * eff["son"]
                if eff["daughter"]:
                    shares["daughter"] = k * eff["daughter"]
            elif eff["father"]:
                asabah_keys = ["father"]
                shares["father"] = shares.get("father", F(0, 1)) + residue
            elif eff["brother_full"]:
                asabah_keys = ["brother_full"] + (["sister_full"] if eff["sister_full"] else [])
                k = residue / (2 * eff["brother_full"] + eff["sister_full"])
                shares["brother_full"] = 2 * k * eff["brother_full"]
                if eff["sister_full"]:
                    shares["sister_full"] = k * eff["sister_full"]
            elif eff["brother_consang"]:
                asabah_keys = ["brother_consang"] + (["sister_consang"] if eff["sister_consang"] else [])
                k = residue / (2 * eff["brother_consang"] + eff["sister_consang"])
                shares["brother_consang"] = 2 * k * eff["brother_consang"]
                if eff["sister_consang"]:
                    shares["sister_consang"] = k * eff["sister_consang"]
            elif eff["daughter"] and eff["sister_full"]:
                asabah_keys = ["sister_full"]
                shares["sister_full"] = residue
            elif eff["daughter"] and eff["sister_consang"]:
                asabah_keys = ["sister_consang"]
                shares["sister_consang"] = residue
            else:
                recipients = {
                    k: s for k, s in shares.items() if k not in _SPOUSE and s > 0
                }
                if recipients:
                    radd_applied = True
                    total_r = sum(recipients.values())
                    for k, s in recipients.items():
                        shares[k] = s + residue * s / total_r
                else:
                    unassigned = residue

    blocked_keys = sorted(k for k in _SIBLINGS if h[k] > 0 and eff[k] == 0)

    net = estate.net if estate is not None else 0
    rows = []
    for key in HEIR_KEYS:
        if eff[key] == 0:
            continue
        group = shares.get(key, F(0, 1))
        if group == 0 and key not in asabah_keys:
            continue
        count = eff[key]
        per = group / count
        amount = None
        each = None
        if estate is not None and estate.has_numbers:
            total = Decimal(net) * Decimal(group.numerator) / Decimal(group.denominator)
            amount = total.quantize(_QUANT)
            each = (Decimal(amount) / count).quantize(_QUANT)
        rows.append(Row(key=key, count=count, share=per, amount=amount, each=each))

    residual = Decimal(0)
    if (
        estate is not None
        and estate.has_numbers
        and rows
        and unassigned is None
    ):
        distributed = sum(((row.each or Decimal(0)) * row.count for row in rows), Decimal(0))
        residual = Decimal(net) - distributed

    return Result(
        rows=rows,
        aul=aul,
        base=base,
        base_from=base_from,
        radd_applied=radd_applied,
        asabah_keys=asabah_keys,
        unassigned=unassigned,
        blocked_keys=blocked_keys,
        residual=residual,
    )