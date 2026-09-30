from decimal import Decimal

import pytest

from app.localization import en, id
from app.localization.localization import CURRENCIES, LANGUAGES, Localization
from fakes import FakeStorage

EN_SUBTITLE = "Faraid Calculator"
ID_SUBTITLE = "Kalkulator Faraid"


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
    assert loc.get("brother_consang") == "Paternal half-brother"
    assert loc.get("sister_consang") == "Paternal half-sister"
    assert loc.get("brother_uterine") == "Maternal half-brother"
    assert loc.get("sister_uterine") == "Maternal half-sister"


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


def test_both_langs_have_identical_keys():
    assert set(en.TRANSLATIONS.keys()) == set(id.TRANSLATIONS.keys())


def test_empty_hint_key_exists_in_both_languages():
    from app.localization import en, id
    assert en.TRANSLATIONS["calc.empty_hint"] == "Run a calculation to see your results here."
    assert id.TRANSLATIONS["calc.empty_hint"] == "Jalankan perhitungan untuk melihat hasil di sini."


def test_new_keys_exist():
    required_new = [
        "settings.title", "settings.language", "settings.currency", "settings.theme",
        "currency.usd", "currency.idr", "currency.myr", "currency.eur", "currency.sgd",
        "theme.light", "theme.dark", "theme.system",
        "info.title", "info.intro.title", "info.intro.body",
        "info.legal_basis.title", "info.legal_basis.quran", "info.legal_basis.hadith",
        "info.how_it_works.title", "info.how_it_works.body",
        "info.glossary.title", "info.glossary.wasiat", "info.glossary.hajb",
        "info.glossary.aul", "info.glossary.radd", "info.glossary.asabah",
        "info.glossary.pewaris", "info.glossary.ahli_waris",
        "info.disclaimer.title", "info.disclaimer.body",
        "about.title", "about.author", "about.location", "about.credits",
        "about.license", "about.github", "about.donate", "about.donate_soon",
    ]
    for k in required_new:
        assert k in en.TRANSLATIONS
        assert k in id.TRANSLATIONS


def test_currency_format_money():
    loc = Localization("en", None)
    loc.currency = "USD"
    assert loc.format_money(1234567) == "$1,234,567.00"
    loc.currency = "IDR"
    assert loc.format_money(1234567) == "1.234.567,00 Rp"
    loc.currency = "EUR"
    assert loc.format_money(1234567) == "1.234.567,00 €"


def test_format_money_keeps_the_cents_the_engine_produced():
    """The faraid engine hands out Decimals quantized to a cent and its odd
    remainders land on half-cents all the time. Grouping the digits of
    `str(Decimal)` would eat the '.' as if it were a thousands separator, so the
    fractional part has to be split off before the integer part is grouped."""
    loc = Localization("en", None)
    loc.currency = "USD"
    assert loc.format_money(Decimal("500000.50")) == "$500,000.50"
    loc.currency = "IDR"
    assert loc.format_money(Decimal("500000.50")) == "500.000,50 Rp"
    loc.currency = "EUR"
    assert loc.format_money(Decimal("500000.50")) == "500.000,50 €"


def test_format_money_rounds_anything_finer_than_a_cent():
    loc = Localization("en", None)
    loc.currency = "USD"
    assert loc.format_money(Decimal("1.005")) == "$1.01"
    assert loc.format_money(Decimal("1234567.894")) == "$1,234,567.89"


def test_format_money_edges():
    loc = Localization("en", None)
    loc.currency = "USD"
    assert loc.format_money(Decimal(0)) == "$0.00"
    assert loc.format_money(Decimal("0.5")) == "$0.50"
    # the sign belongs outside the symbol, whichever side the symbol sits on
    assert loc.format_money(Decimal("-1234.5")) == "-$1,234.50"
    loc.currency = "IDR"
    assert loc.format_money(Decimal("-1234.5")) == "-1.234,50 Rp"


def test_format_money_does_not_invent_a_sign_on_a_negative_that_rounds_to_zero():
    loc = Localization("en", None)
    loc.currency = "USD"
    assert loc.format_money(Decimal("-0.004")) == "$0.00"


def test_format_money_handles_an_amount_wider_than_the_decimal_context():
    """The engine runs with a 28-digit decimal context, and quantize() rounds
    within it, so an amount with more integer digits than that would raise
    instead of rendering. The estate fields cap nothing, so one is typeable."""
    loc = Localization("en", None)
    loc.currency = "USD"
    huge = 10 ** 30
    assert loc.format_money(huge) == "$1,000,000,000,000,000,000,000,000,000,000.00"


def test_format_money_reads_an_int_as_whole_currency_units():
    """An int is a whole amount, so it keeps the '.00' it always showed; the same
    value as a Decimal must come out identical, or the page would change an
    amount's cents depending on which type the engine happened to produce."""
    loc = Localization("en", None)
    loc.currency = "USD"
    assert loc.format_money(500000) == "$500,000.00"
    assert loc.format_money(500000) == loc.format_money(Decimal("500000.00"))
    assert loc.format_money(500000) == loc.format_money(Decimal(500000))
