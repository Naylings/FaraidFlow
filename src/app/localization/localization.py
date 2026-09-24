# src/app/localization/localization.py

from . import en, id  # language tables

LANGUAGES = [
    {"code": "en", "label": "English", "flag": "🇬🇧"},
    {"code": "id", "label": "Bahasa Indonesia", "flag": "🇮🇩"},
]

_CODES = {lang["code"] for lang in LANGUAGES}
_TABLES = {"en": en, "id": id}


class Localization:
    STORAGE_KEY = "faraidflow.lang"

    def __init__(self, language: str, storage):
        self.language = language
        self.storage = storage

    @classmethod
    async def load(cls, storage, default_language: str = "en") -> "Localization":
        language = default_language
        try:
            stored = await storage.get(cls.STORAGE_KEY)
        except Exception:  # noqa: BLE001 - storage may be unavailable; fall back to default
            stored = None
        if stored in _CODES:
            language = stored
        return cls(language, storage)

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