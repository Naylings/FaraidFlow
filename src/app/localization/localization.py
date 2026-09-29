# src/app/localization/localization.py

from decimal import ROUND_HALF_UP, Decimal, localcontext

from . import en, id  # language tables

LANGUAGES = [
    {"code": "en", "label": "English", "flag": "🇬🇧"},
    {"code": "id", "label": "Bahasa Indonesia", "flag": "🇮🇩"},
]

CURRENCIES = [
    {"code": "USD", "symbol": "$", "position": "prefix", "thousands": ",", "decimal": "."},
    {"code": "IDR", "symbol": "Rp", "position": "postfix", "thousands": ".", "decimal": ","},
    {"code": "MYR", "symbol": "RM", "position": "prefix", "thousands": ",", "decimal": "."},
    {"code": "EUR", "symbol": "€", "position": "postfix", "thousands": ".", "decimal": ","},
    {"code": "SGD", "symbol": "S$", "position": "prefix", "thousands": ",", "decimal": "."},
]

THEMES = [
    {"code": "light", "label_key": "theme.light"},
    {"code": "dark", "label_key": "theme.dark"},
    {"code": "system", "label_key": "theme.system"},
]

STORAGE_KEYS = {
    "language": "faraidflow.lang",
    "currency": "faraidflow.currency",
    "theme": "faraidflow.theme",
}

_CODES = {lang["code"] for lang in LANGUAGES}
_TABLES = {"en": en, "id": id}
_CENTS = Decimal("0.01")


def _group(digits: str, sep: str) -> str:
    """Group a plain digit string in threes, e.g. '1234567' -> '1,234,567'."""
    head = len(digits) % 3 or 3
    return sep.join([digits[:head], *(digits[i:i + 3] for i in range(head, len(digits), 3))])


class Localization:
    STORAGE_KEY = "faraidflow.lang"

    def __init__(self, language: str, storage):
        self.language = language
        self.storage = storage
        self._currency = "USD"
        self._theme = "system"

    @classmethod
    async def load(cls, storage, default_language: str = "en") -> "Localization":
        language = default_language
        currency = "USD"
        theme = "system"
        try:
            stored_lang = await storage.get(cls.STORAGE_KEY)
            stored_currency = await storage.get(STORAGE_KEYS["currency"])
            stored_theme = await storage.get(STORAGE_KEYS["theme"])
        except Exception:  # noqa: BLE001 - storage may be unavailable; fall back to default
            stored_lang = stored_currency = stored_theme = None
        if stored_lang in _CODES:
            language = stored_lang
        if stored_currency in {c["code"] for c in CURRENCIES}:
            currency = stored_currency
        if stored_theme in {t["code"] for t in THEMES}:
            theme = stored_theme
        loc = cls(language, storage)
        loc._currency = currency
        loc._theme = theme
        return loc

    def get(self, key: str) -> str:
        table = _TABLES[self.language]
        return table.TRANSLATIONS.get(key, key)

    async def set_language(self, code: str) -> None:
        if code not in _CODES:
            raise ValueError(f"Unknown language: {code}")
        self.language = code
        try:
            await self.storage.set(self.STORAGE_KEY, code)
        except Exception:  # noqa: BLE001, S110 - persistence failures must not break the app
            pass

    @property
    def currency(self) -> str:
        return self._currency

    @currency.setter
    def currency(self, code: str) -> None:
        if code not in {c["code"] for c in CURRENCIES}:
            raise ValueError(f"Unknown currency: {code}")
        self._currency = code

    async def set_currency(self, code: str) -> None:
        self.currency = code
        try:
            await self.storage.set(STORAGE_KEYS["currency"], code)
        except Exception:  # noqa: BLE001, S110
            pass

    @property
    def theme(self) -> str:
        return self._theme

    @theme.setter
    def theme(self, code: str) -> None:
        if code not in {t["code"] for t in THEMES}:
            raise ValueError(f"Unknown theme: {code}")
        self._theme = code

    async def set_theme(self, code: str) -> None:
        self.theme = code
        try:
            await self.storage.set(STORAGE_KEYS["theme"], code)
        except Exception:  # noqa: BLE001, S110
            pass

    def format_money(self, amount: int | Decimal) -> str:
        """Render an amount in the selected currency, at two decimal places.

        The faraid engine produces `Decimal` amounts, and its odd remainders
        land on half-cents (a 1,000,001 estate shared by a husband and a son is
        250,000.25 / 750,000.75), so the fractional part is real data and has to
        be split off before the integer part is grouped -- grouping the digits of
        `str(Decimal)` would eat the '.' as if it were a thousands separator. An
        `int` is read as whole currency units, which is what the engine's inputs
        are, and so it shows the trailing zeros the amounts have always shown.
        """
        curr = next(c for c in CURRENCIES if c["code"] == self._currency)
        value = Decimal(amount)
        with localcontext() as ctx:
            # Both quantize and Decimal's own formatting round within the context,
            # whose 28 digits the engine sets globally, so an amount wider than
            # that would raise. The estate fields cap nothing, so one is
            # typeable; widen the context to fit whatever came in.
            ctx.prec = max(ctx.prec, len(value.as_tuple().digits) + 2)
            rounded = value.quantize(_CENTS, rounding=ROUND_HALF_UP)
            whole, _, frac = f"{abs(rounded):f}".partition(".")
        # The sign comes off the rounded value, so a negative that rounds to zero
        # (a -0.004) reads as plain zero instead of "-$0.00".
        sign = "-" if rounded < 0 else ""
        digits = f"{_group(whole, curr['thousands'])}{curr['decimal']}{frac}"
        if curr["position"] == "prefix":
            return f"{sign}{curr['symbol']}{digits}"
        return f"{sign}{digits} {curr['symbol']}"