import pytest

from app.localization.localization import LANGUAGES, Localization
from fakes import FakeStorage

EN_SUBTITLE = "Islamic Inheritance Calculator"
ID_SUBTITLE = "Ahli Waris"


async def test_default_english_when_nothing_saved():
    loc = await Localization.load(FakeStorage(), default_language="en")
    assert loc.language == "en"
    assert loc.get("home.subtitle") == EN_SUBTITLE
    assert loc.get("calculate") == "Calculate"


async def test_loads_saved_language():
    storage = FakeStorage()
    await storage.set(Localization.STORAGE_KEY, "id")
    loc = await Localization.load(storage, default_language="en")
    assert loc.language == "id"
    assert loc.get("calculate") == "Hitung"
    assert loc.get("home.subtitle") == ID_SUBTITLE


async def test_unknown_saved_language_falls_back_to_default():
    storage = FakeStorage()
    await storage.set(Localization.STORAGE_KEY, "fr")
    loc = await Localization.load(storage, default_language="en")
    assert loc.language == "en"


async def test_storage_failure_falls_back_to_default():
    storage = FakeStorage()

    async def boom_get(key, default=None):
        raise RuntimeError("storage unavailable")

    storage.get = boom_get
    loc = await Localization.load(storage, default_language="en")
    assert loc.language == "en"


async def test_set_language_switches_and_persists():
    storage = FakeStorage()
    loc = await Localization.load(storage, default_language="en")
    await loc.set_language("id")
    assert loc.language == "id"
    assert loc.get("about") == "Tentang"
    assert (await storage.get(Localization.STORAGE_KEY)) == "id"
    await loc.set_language("en")
    assert loc.get("about") == "About"
    assert (await storage.get(Localization.STORAGE_KEY)) == "en"


async def test_set_language_save_failure_is_not_fatal():
    storage = FakeStorage()
    loc = await Localization.load(storage, default_language="en")

    async def boom_set(key, value):
        raise RuntimeError("storage unavailable")

    loc.storage.set = boom_set
    await loc.set_language("id")
    assert loc.language == "id"


async def test_missing_key_returns_key():
    loc = await Localization.load(FakeStorage(), default_language="en")
    assert loc.get("no.such.key") == "no.such.key"


def test_languages_metadata():
    codes = {lang["code"] for lang in LANGUAGES}
    assert codes == {"en", "id"}
    by_code = {lang["code"]: lang for lang in LANGUAGES}
    assert by_code["en"]["flag"] == "🇬🇧"
    assert by_code["id"]["flag"] == "🇮🇩"