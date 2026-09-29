# src/app/localization/localization.py

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

    def format_money(self, amount: int) -> str:
        curr = next(c for c in CURRENCIES if c["code"] == self._currency)
        symbol = curr["symbol"]
        thousands_sep = curr["thousands"]
        decimal_sep = curr["decimal"]
        position = curr["position"]

        # Format integer part with thousands separator
        s = str(amount)
        if len(s) <= 3:
            int_part = s
        else:
            parts = []
            while len(s) > 3:
                parts.append(s[-3:])
                s = s[:-3]
            parts.append(s)
            int_part = thousands_sep.join(reversed(parts))

        # Decimal part (always .00 since amount is integer representing cents)
        dec_part = "00"

        if position == "prefix":
            return f"{symbol}{int_part}{decimal_sep}{dec_part}"
        else:
            return f"{int_part}{decimal_sep}{dec_part} {symbol}"