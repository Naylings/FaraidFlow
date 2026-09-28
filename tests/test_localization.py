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


async def test_sibling_labels_english_drop_indonesian_notes():
    loc = await Localization.load(FakeStorage(), default_language="en")
    assert loc.get("brother_full") == "Full brother"
    assert loc.get("sister_full") == "Full sister"
    assert loc.get("brother_consang") == "Paternal brother"
    assert loc.get("sister_consang") == "Paternal sister"
    assert loc.get("brother_uterine") == "Maternal brother"
    assert loc.get("sister_uterine") == "Maternal sister"


async def test_sibling_labels_indonesian_use_saudara_saudari():
    storage = FakeStorage()
    await storage.set(Localization.STORAGE_KEY, "id")
    loc = await Localization.load(storage, default_language="en")
    assert loc.get("brother_full") == "Saudara kandung"
    assert loc.get("sister_full") == "Saudari kandung"
    assert loc.get("brother_consang") == "Saudara seayah"
    assert loc.get("sister_consang") == "Saudari seayah"
    assert loc.get("brother_uterine") == "Saudara seibu"
    assert loc.get("sister_uterine") == "Saudari seibu"


async def test_money_entries_present():
    loc = await Localization.load(FakeStorage(), default_language="en")
    assert loc.get("money.prefix") == "$"
    assert loc.get("money.thousands_sep") == ","
    assert loc.get("money.decimal_sep") == "."


async def test_new_calc_keys_present_both_languages():
    en = await Localization.load(FakeStorage(), default_language="en")
    id = await Localization.load(FakeStorage(), default_language="id")
    keys = ("calc.details", "calc.equal", "calc.blocked", "calc.blocked_tip",
            "calc.residual", "calc.col_each", "calc.col_total",
            "calc.block.reason.lineal", "calc.block.reason.full_brother",
            "calc.block.reason.uterine")
    for key in keys:
        assert en.get(key) != key, f"missing EN key {key}"
        assert id.get(key) != key, f"missing ID key {key}"