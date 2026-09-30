import flet as ft

from app.calculation import estate as estate_mod
from app.localization.localization import Localization
from app.pages.calculate import CalculationPage, is_two_pane
from fakes import FakePage, FakeStorage


class _Ev:
    """Minimal stand-in for a Flet change/key event."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


async def _page(language="en", width=None):
    loc = await Localization.load(FakeStorage(), default_language="en")
    pg = FakePage()
    if width is not None:
        pg.width = width
    calc = CalculationPage(pg, loc, back_home=lambda: None)
    return calc, pg, loc


def _children(control):
    items = list(getattr(control, "controls", None) or [])
    for attr in ("rows", "columns", "cells"):
        children = getattr(control, attr, None)
        if isinstance(children, list):
            for child in children:
                if isinstance(child, ft.Control):
                    items.append(child)
    for attr in ("content", "label"):
        child = getattr(control, attr, None)
        if child is not None and isinstance(child, ft.Control):
            items.append(child)
    return items


def _walk(control):
    yield control
    for c in _children(control):
        yield from _walk(c)


def _by_key(control, key):
    if getattr(control, "key", None) == key:
        return control
    for c in _children(control):
        found = _by_key(c, key)
        if found is not None:
            return found
    return None


def _buttons(calc):
    return [c for c in _walk(calc.build()) if isinstance(c, ft.FilledButton)]


async def test_form_build_contains_estate_fields_and_calculate():
    calc, pg, _ = await _page()
    root = calc.build()
    assert _by_key(root, "estate-gross") is not None
    assert _by_key(root, "estate-funeral") is not None
    assert _by_key(root, "estate-debts") is not None
    assert _by_key(root, "estate-wasiat") is not None
    assert _by_key(root, "btn-calculate") is not None


async def test_calculate_produces_result_rows():
    calc, pg, _ = await _page()
    calc.heirs = {"son": 1, "daughter": 1}
    calc._compute()
    assert calc.calc_result is not None
    assert {r.key for r in calc.calc_result.rows} == {"son", "daughter"}


async def test_fractions_only_when_no_numbers():
    calc, pg, _ = await _page()
    calc.heirs = {"son": 1, "father": 1}
    calc._compute()
    assert calc.calc_result.rows[0].amount is None


async def test_result_card_shows_breakdown_with_wasiat():
    calc, pg, loc = await _page()
    from app.calculation.estate import Estate

    calc.heirs = {"daughter": 1, "father": 1}
    calc.estate = Estate(gross=600_000_000, funeral=20_000_000, debts=100_000_000, wasiat=30_000_000)
    calc._compute()
    texts = [c.value for c in _walk(calc._build_result()) if isinstance(c, ft.Text)]
    assert any(t and loc.get("calc.wasiat") in t for t in texts)


async def test_tree_shows_deceased_and_selected_branches():
    calc, pg, loc = await _page()
    calc.heirs = {"son": 2, "daughter": 1}
    calc.estate = estate_mod.Estate()
    calc._compute()
    texts = [c.value for c in _walk(calc.build()) if isinstance(c, ft.Text)]
    assert "Deceased" in texts or loc.get("calc.deceased") in texts
    assert "Sons" in texts


async def test_form_estate_fields_are_numeric_and_page_scrolls():
    calc, pg, _ = await _page()
    root = calc.build()
    assert getattr(root, "scroll", None) == ft.ScrollMode.AUTO
    assert getattr(root, "expand", None) is True
    for key in ("estate-gross", "estate-funeral", "estate-debts", "estate-wasiat"):
        tf = _by_key(root, key)
        assert tf is not None
        assert getattr(tf, "keyboard_type", None) == ft.KeyboardType.NUMBER
        assert getattr(tf, "input_filter", None) is not None
        assert isinstance(getattr(tf, "input_filter", None), ft.InputFilter)
    card_col = _by_key(root, "col-cards")
    assert card_col is not None
    assert getattr(card_col, "horizontal_alignment", None) == ft.CrossAxisAlignment.STRETCH


async def test_estate_field_groups_input_commas():
    calc, pg, _ = await _page()
    root = calc.build()
    gross = _by_key(root, "estate-gross")
    assert gross is not None
    gross.value = "5000000"
    calc._collect()
    assert calc.estate.gross == 5000000


async def test_estate_input_accepts_commas_and_strips_on_parse():
    calc, pg, _ = await _page()
    root = calc.build()
    calc._tf["estate-gross"].value = "12,345,678"
    calc._collect()
    assert calc.estate.gross == 12345678


async def test_capture_state_none_before_build():
    calc, _, _ = await _page()
    assert calc.capture_state() is None


async def test_restore_state_none_is_noop():
    calc, _, _ = await _page()
    calc.build()
    calc.restore_state(None)
    assert calc.capture_state()["has_result"] is False


async def test_capture_restore_round_trip_preserves_state():
    calc, _, _ = await _page()
    calc.build()
    calc._tf["estate-gross"].value = "5,000,000"
    calc._spouse.value = "wife"
    calc._wife_count.value = "2"
    calc._count_fields["daughter"].value = "2"
    calc._parent_checkboxes["father"].value = True
    state = calc.capture_state()
    assert state["tf"]["estate-gross"] == "5,000,000"
    assert state["spouse"] == "wife"
    assert state["counts"]["daughter"] == "2"
    assert state["parents"]["father"] is True
    assert state["has_result"] is False
    calc.build()
    calc.restore_state(state)
    assert calc._tf["estate-gross"].value == "5,000,000"
    assert calc._spouse.value == "wife"
    assert calc._count_fields["daughter"].value == "2"
    assert calc._parent_checkboxes["father"].value is True


async def test_restore_state_regenerates_result_in_new_language():
    calc, _, loc = await _page("en")
    calc.build()
    calc._tf["estate-gross"].value = "6000000"
    calc._spouse.value = "husband"
    calc._count_fields["daughter"].value = "1"
    calc._collect()
    calc._compute()
    state = calc.capture_state()
    assert state["has_result"] is True
    assert _by_key(calc.build(), "result-table") is not None
    await loc.set_language("id")
    calc.build()
    calc.restore_state(state)
    texts = [c.value for c in _walk(calc.result_card) if isinstance(c, ft.Text)]
    assert any("Suami" in (v or "") for v in texts)


from app.pages.calculate import _fmt_int


def test_fmt_int_groups_thousands():
    assert _fmt_int(5000000) == "5,000,000"
    assert _fmt_int(0) == "0"


def test_parse_int_strips_commas():
    from app.pages.calculate import _parse_int
    assert _parse_int("12,345") == 12345
    assert _parse_int("") == 0
    assert _parse_int("abc") == 0


async def test_result_amounts_follow_the_chosen_currency():
    """Every amount on the result page is rendered by Localization.format_money,
    so picking a currency in settings re-renders the table in that currency's
    symbol and separators."""
    calc, pg, loc = await _page()
    loc.currency = "IDR"
    calc.heirs = {"son": 1}
    calc.estate = estate_mod.Estate(gross=1234567)
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    cells = [c.value for row in table.controls[2:] for c in row.controls]
    assert "$" not in "".join(cells)
    assert any("1.234.567,00 Rp" in v for v in cells), cells


async def test_result_amounts_keep_the_cents_the_engine_produced():
    """Faraid's odd remainders land on half-cents: 1,000,001 shared by a husband
    and a son is 250,000.25 / 750,000.75. Rounding those to whole dollars, or
    grouping the '.' of the Decimal as if it were a thousands separator, would
    quietly change the answer the table gives."""
    calc, pg, _ = await _page()
    calc.heirs = {"husband": 1, "son": 1}
    calc.estate = estate_mod.Estate(gross=1000001)
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    cells = [c.value for row in table.controls[2:] for c in row.controls]
    assert "$250,000.25" in cells
    assert "$750,000.75" in cells


async def test_breakdown_line_follows_the_chosen_currency():
    calc, pg, loc = await _page()
    loc.currency = "EUR"
    calc.heirs = {"son": 1}
    calc.estate = estate_mod.Estate(gross=1234567, funeral=1000, debts=2000, wasiat=3000)
    calc._compute()
    line = next(
        c.value for c in _walk(calc._build_result())
        if isinstance(c, ft.Text) and c.value and loc.get("calc.gross") in c.value
    )
    assert "1.234.567,00 €" in line
    assert "1.000,00 €" in line


async def test_wasiat_cap_and_excess_follow_the_chosen_currency():
    calc, pg, loc = await _page()
    loc.currency = "IDR"
    calc.heirs = {"son": 1}
    calc.estate = estate_mod.Estate(gross=1000, wasiat=500)
    calc._compute()
    warn = next(
        c.value for c in _walk(calc._build_result())
        if isinstance(c, ft.Text) and c.value and loc.get("calc.wasiat_warn") in c.value
    )
    assert "333,00 Rp" in warn
    assert "167,00 Rp" in warn


async def test_depleted_claim_follows_the_chosen_currency():
    calc, pg, loc = await _page()
    loc.currency = "IDR"
    calc.heirs = {"son": 1}
    calc.estate = estate_mod.Estate(gross=100, debts=250)
    calc._compute()
    claim = next(
        c.value for c in _walk(calc._build_result())
        if isinstance(c, ft.Text) and c.value and loc.get("calc.depleted").split("{")[0] in c.value
    )
    assert "150,00 Rp" in claim


async def test_residual_note_follows_the_chosen_currency():
    """The residual is the leftover from flooring each heir's per-person amount,
    so it is itself a fractional amount and has to survive the same way."""
    calc, pg, loc = await _page()
    loc.currency = "IDR"
    calc.heirs = {"wife": 1, "son": 3}
    calc.estate = estate_mod.Estate(gross=1000)
    calc._compute()
    note = next(
        c.value for c in _walk(calc._build_result())
        if isinstance(c, ft.Text) and c.value and loc.get("calc.residual").split("{")[0] in c.value
    )
    assert "0,02 Rp" in note


async def test_total_column_shows_a_dash_when_there_is_no_amount():
    """The no-numbers case has no amount to format at all, and '-' is what the
    columns have always shown; the money formatter must not be handed a None."""
    calc, pg, _ = await _page()
    calc.heirs = {"son": 1, "father": 1}
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    rows = [[c.value for c in r.controls] for r in table.controls[2:]]
    assert [row[-1] for row in rows] == ["-", "-"]


async def test_each_column_shows_a_dash_when_there_is_no_amount():
    """Two sons with no numbers entered is the only shape that shows the per-person
    column at all, and it is exactly the shape where there is no per-person amount."""
    calc, pg, _ = await _page()
    calc.heirs = {"son": 2}
    calc.estate = estate_mod.Estate()
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    rows = [[c.value for c in r.controls] for r in table.controls[2:]]
    assert [row[2:] for row in rows] == [["-", "-"]]


async def test_wife_count_disabled_by_default_and_enabled_on_wife():
    calc, pg, _ = await _page()
    root = calc.build()
    wife = _by_key(root, "count-wife")
    assert wife is not None
    assert wife.disabled is True
    calc._spouse.value = "wife"
    calc._spouse.on_change(None)
    assert calc._wife_count.disabled is False


async def test_parents_are_checkboxes_without_count_fields():
    calc, pg, _ = await _page()
    root = calc.build()
    checks = [c for c in _walk(root) if isinstance(c, ft.Checkbox)]
    assert {c.key for c in checks} >= {"father", "mother"}
    assert "father" not in calc._count_fields
    assert "mother" not in calc._count_fields


async def test_heir_counts_are_number_fields_not_dropdowns():
    calc, pg, _ = await _page()
    root = calc.build()
    for key in ("son", "daughter", "brother_full", "sister_uterine"):
        field = _by_key(root, f"count-{key}")
        assert field is not None
        assert isinstance(field, ft.TextField)
        assert not isinstance(field, ft.Dropdown)


HEIR_COUNT_KEYS = (
    "son", "daughter",
    "brother_full", "sister_full",
    "brother_consang", "sister_consang",
    "brother_uterine", "sister_uterine",
)


async def test_heir_counts_prefilled_with_zero_like_the_estate_fields():
    calc, pg, _ = await _page()
    root = calc.build()
    for key in HEIR_COUNT_KEYS:
        field = _by_key(root, f"count-{key}")
        assert field is not None, key
        assert field.value == "0", key
    # the estate block already defaulted to "0"; the form must now match it
    for key in ("estate-gross", "estate-funeral", "estate-debts", "estate-wasiat"):
        assert _by_key(root, key).value == "0", key


async def test_every_heir_label_sits_in_a_fixed_width_column():
    calc, pg, loc = await _page()
    root = calc.build()
    wanted = {loc.get(k) for k in HEIR_COUNT_KEYS}
    labels = {c.value: c for c in _walk(root) if isinstance(c, ft.Text) and c.value in wanted}
    assert set(labels) == wanted, "every count-field heir must render exactly one label"
    for text in labels.values():
        assert text.width == 150, text.value
        assert text.no_wrap is True, text.value
        assert text.overflow == ft.TextOverflow.ELLIPSIS, text.value


def _paired_rows(root):
    """Map a sorted (first, second) heir-key tuple to the ResponsiveRow holding it."""
    wanted = {f"count-{k}" for k in HEIR_COUNT_KEYS}
    found = {}
    for control in _walk(root):
        if not isinstance(control, ft.ResponsiveRow):
            continue
        keys = {
            c.key[len("count-"):]
            for c in _walk(control)
            # result_card carries an unhashable ft.ScrollKey; only string keys count
            if isinstance(getattr(c, "key", None), str) and c.key in wanted
        }
        if len(keys) == 2:
            found[tuple(sorted(keys))] = control
    return found


async def test_heir_fields_are_paired_two_up_in_a_responsive_row():
    calc, pg, _ = await _page()
    root = calc.build()
    pairs = _paired_rows(root)
    assert set(pairs) == {
        ("daughter", "son"),
        ("brother_full", "sister_full"),
        ("brother_consang", "sister_consang"),
        ("brother_uterine", "sister_uterine"),
    }, sorted(pairs)
    for keys, row in pairs.items():
        assert len(row.controls) == 2, keys
        for cell in row.controls:
            assert cell.col in (6, 12), keys


async def test_parent_checkboxes_are_paired_in_a_responsive_row():
    calc, pg, _ = await _page()
    root = calc.build()
    candidates = [
        r
        for r in (c for c in _walk(root) if isinstance(c, ft.ResponsiveRow))
        if {"father", "mother"} <= {
            c.key for c in _walk(r) if isinstance(getattr(c, "key", None), str)
        }
    ]
    # the page-level ResponsiveRow also contains both, so take the innermost one
    parent_row = min(candidates, key=lambda r: sum(1 for _ in _walk(r)))
    assert len(parent_row.controls) == 2
    for cell in parent_row.controls:
        assert cell.col in (6, 12)
        assert len([c for c in _walk(cell) if isinstance(c, ft.Checkbox)]) == 1


async def test_untouched_form_with_zero_counts_shows_no_heirs_error():
    calc, pg, _ = await _page()
    calc.build()
    calc._collect()
    calc._compute()
    assert calc.calc_result.errors == ["calc.errors.no_heirs"]
    assert calc.calc_result.rows == []
    assert calc._wife_count.value == "1"


async def test_each_column_hidden_when_all_single():
    calc, pg, _ = await _page()
    calc.heirs = {"son": 1}
    calc.estate = estate_mod.Estate(gross=60000000)
    calc._compute()
    result = calc._build_result()
    table = _by_key(result, "result-table")
    assert table is not None
    headers = [c.value for c in table.controls[0].controls]
    assert "Each" not in headers


async def test_each_column_shown_when_multiple():
    calc, pg, _ = await _page()
    calc.heirs = {"son": 2}
    calc.estate = estate_mod.Estate(gross=90000000)
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    headers = [c.value for c in table.controls[0].controls]
    assert headers[-3:] == ["Share", "Per Person", "Total Amount"]


async def test_amounts_display_with_dollar_and_two_decimals():
    calc, pg, _ = await _page()
    calc.heirs = {"daughter": 1}
    calc.estate = estate_mod.Estate(gross=100)
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    cells = [c.value for row in table.controls[2:] for c in row.controls]
    assert any("$" in v for v in cells)


async def test_share_column_shows_group_share_not_per_person_share():
    # Wife + 2 sons: wife 1/8, sons share 7/8 between them.
    # The row is labelled "Sons x2" and its Total is the whole group total,
    # so the Share cell must be the group share (7/8), not the per-person 7/16.
    calc, pg, _ = await _page()
    calc.heirs = {"wife": 1, "son": 2}
    calc.estate = estate_mod.Estate(gross=1000)
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    rows = {r.controls[0].value: [c.value for c in r.controls] for r in table.controls[2:]}
    assert rows["Sons  x2"][1] == "7/8"
    assert rows["Wife"][1] == "1/8"
    # per-person share 7/16 must not leak into the table
    assert all(v[1] != "7/16" for v in rows.values())


async def test_share_column_matches_total_column_basis_for_groups():
    calc, pg, _ = await _page()
    calc.heirs = {"son": 3}
    calc.estate = estate_mod.Estate(gross=9000)
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    row = [c.value for c in table.controls[2].controls]
    # group share 1 -> share cell "1", each 3000, total 9000
    assert row[1] == "1"
    assert row[2] == "$3,000.00"
    assert row[3] == "$9,000.00"


async def test_result_table_cells_expand_to_fill_container():
    calc, pg, _ = await _page()
    calc.heirs = {"son": 2, "daughter": 1}
    calc.estate = estate_mod.Estate(gross=100)
    calc._compute()
    table = _by_key(calc._build_result(), "result-table")
    assert table is not None
    for row in table.controls:
        if not isinstance(row, ft.Row):
            continue
        assert all(c.expand for c in row.controls), "every cell must expand"
    assert sum(c.expand for c in table.controls[0].controls) > 0


async def test_result_table_expands_with_and_without_each_column():
    calc, pg, _ = await _page()
    calc.estate = estate_mod.Estate(gross=100)
    calc.heirs = {"son": 2}
    calc._compute()
    with_each = _by_key(calc._build_result(), "result-table")
    calc.heirs = {"son": 1}
    calc._compute()
    without_each = _by_key(calc._build_result(), "result-table")
    assert len(with_each.controls[0].controls) == 4
    assert len(without_each.controls[0].controls) == 3
    for table in (with_each, without_each):
        assert all(c.expand for c in table.controls[0].controls)
        for row in table.controls[2:]:
            assert all(c.expand for c in row.controls)


async def test_debt_note_only_when_unpaid():
    calc, pg, loc = await _page()
    calc.heirs = {"son": 1}
    calc.estate = estate_mod.Estate(gross=100, funeral=10, debts=20)
    calc._compute()
    texts = [c.value for c in _walk(calc._build_result()) if isinstance(c, ft.Text)]
    assert not any(t and "Debts are not inherited" in t for t in texts)


async def test_debt_note_shown_when_unpaid():
    calc, pg, loc = await _page()
    calc.heirs = {"son": 1}
    calc.estate = estate_mod.Estate(gross=100, funeral=10, debts=120)
    calc._compute()
    texts = [c.value for c in _walk(calc._build_result()) if isinstance(c, ft.Text)]
    assert any(t and "Debts are not inherited" in t for t in texts)


async def test_no_heirs_error_suppresses_others():
    calc, pg, _ = await _page()
    calc.heirs = {}
    calc.estate = estate_mod.Estate(gross=100)
    calc._compute()
    errs = [c.value for c in _walk(calc._build_result()) if isinstance(c, ft.Text) and c.color == ft.Colors.ERROR]
    assert errs == ["Select at least one heir."]


async def test_section_headings_localize_in_id():
    loc = await Localization.load(FakeStorage(), default_language="en")
    await loc.set_language("id")
    pg = FakePage()
    calc = CalculationPage(pg, loc, back_home=lambda: None)
    root = calc.build()
    texts = [c.value for c in _walk(root) if isinstance(c, ft.Text)]
    assert "Anak" in texts
    assert "Orang Tua" in texts
    assert "Saudara" in texts


from fractions import Fraction as F


def test_equivalence_lines_from_group_shares():
    from app.calculation.engine import Row
    from app.pages.calculate import _equivalence_lines
    rows = [
        Row(key="husband", count=1, share=F(1, 2)),
        Row(key="father", count=1, share=F(1, 3)),
        Row(key="mother", count=1, share=F(1, 6)),
    ]
    lines = _equivalence_lines(rows)
    assert lines == ["1/2 = 3/6", "1/3 = 2/6", "1/6 = 1/6"]


async def test_tree_marks_blocked_sibling_disabled():
    calc, pg, _ = await _page()
    calc.heirs = {"brother_full": 1, "brother_consang": 1}
    calc.estate = estate_mod.Estate()
    calc._compute()
    root = calc.build()
    chips = [c for c in _walk(root) if isinstance(c, ft.Chip) and c.label.value.startswith("Paternal")]
    assert chips
    assert all(chip.disabled for chip in chips)
    assert all(chip.tooltip is not None for chip in chips)


async def test_tree_fills_pane_and_splits_width_by_expand():
    """Chips live in the result pane, a fraction of the window. The tree must fill
    that pane and share it out with expand, never with window breakpoints, and its
    text must be clipped with a tooltip instead of spilling over a neighbour."""
    calc, pg, _ = await _page()
    calc.heirs = {"son": 2, "daughter": 1, "brother_full": 1}
    calc.estate = estate_mod.Estate()
    calc._compute()
    root = calc.build()

    tree = next(
        c for c in _walk(root)
        if isinstance(c, ft.Card)
        and any(isinstance(x, ft.Chip) for x in _walk(c))
    )
    # the tree card must claim the full width of the pane
    body = tree.content
    assert getattr(body, "expand", None) is True

    branch_rows = [c for c in _walk(tree) if isinstance(c, ft.Row) and c.spacing]
    assert branch_rows
    row = next(r for r in branch_rows if len(r.controls) > 1)
    assert row.wrap is not True, "expand and wrap cannot share a Row"
    # width is divided by expand + gutter, resolved against the real container
    for branch in row.controls:
        assert getattr(branch, "expand", None) == 1
        assert not isinstance(branch.col, dict), "window spans cause the overlap"

    chips = [c for c in _walk(root) if isinstance(c, ft.Chip)]
    assert chips
    for chip in chips:
        assert chip.label.no_wrap is True
        assert chip.label.overflow == ft.TextOverflow.ELLIPSIS
        assert chip.tooltip, "clipped chip text must stay readable via tooltip"


async def test_tree_omits_a_section_that_has_no_heirs():
    """Selecting 'no spouse' must not leave an empty Spouse heading on the tree."""
    calc, pg, loc = await _page()
    calc.heirs = {"son": 2}
    calc.estate = estate_mod.Estate()
    calc._compute()
    calc.build()
    without = [x.value for x in _walk(calc.result_card) if isinstance(x, ft.Text)]
    assert loc.get("calc.spouse") not in without
    assert loc.get("calc.children") in without

    calc2, _pg2, loc2 = await _page()
    calc2.heirs = {"wife": 1, "son": 2}
    calc2.estate = estate_mod.Estate()
    calc2._compute()
    calc2.build()
    with_spouse = [
        x.value for x in _walk(calc2.result_card) if isinstance(x, ft.Text)
    ]
    assert loc2.get("calc.spouse") in with_spouse


async def test_count_field_is_always_one_plain_number():
    """Counts follow the estate fields' own formatting: always a single plain
    number, never blank, never negative, never carrying stray characters."""
    calc, pg, _ = await _page()
    root = calc.build()
    field = _by_key(root, "count-son")
    assert field is not None
    assert isinstance(field, ft.TextField)
    assert field.value == "0"
    assert isinstance(field.input_filter, ft.InputFilter)
    assert field.on_change is not None

    def type_in(text):
        field.value = text
        field.on_change(_Ev(control=field))
        return field.value

    assert type_in("") == "0", "blank snaps back to a real number"
    assert type_in("007") == "7", "stray leading zeros are normalised"
    assert type_in("1,2") == "12", "separators typed by hand are stripped"
    assert type_in("12a") == "12", "letters are dropped"
    assert type_in("3") == "3", "a plain number is left alone"


async def test_heir_pairs_follow_the_pane_not_the_window():
    """Regression: the heir card used to ask for two fields side by side based on
    `page.width`, but it sits in the form pane, which in two-pane mode is half the
    window. Between ~992 and ~1180 that produced two cells too narrow to hold a
    150px label and an entry, and the fields overlapped."""
    from app.pages.calculate import LABEL_WIDTH, MIN_FIELD_WIDTH

    async def _spans(width):
        calc, pg, _ = await _page(width=width)
        root = calc.build()
        rows = [
            r
            for r in _walk(root)
            if isinstance(r, ft.ResponsiveRow)
            and "count-son" in {
                x.key for x in _walk(r) if isinstance(getattr(x, "key", None), str)
            }
        ]
        # the page-level ResponsiveRow contains count-son deeper down; take the
        # innermost one, which is the actual pair of heir fields
        inner = min(rows, key=lambda r: sum(1 for _ in _walk(r)))
        return {c.col for c in inner.controls}

    # cramped panes stack. 992-1100 is where the fields were too tight to use
    for width in (992, 1000, 1024, 1100):
        assert await _spans(width) == {12}, f"too cramped at window width {width}"

    # 1167 and up leave the entry a comfortable ~105px, so pairing is kept
    for width in (1167, 1180, 1400, 1600):
        assert await _spans(width) == {6}, f"should pair at window width {width}"

    # the decision is driven by the pane, so stacked mode pairs far earlier
    assert await _spans(700) == {6}

    # the entry can never push past its own cell
    calc, pg, _ = await _page(width=1167)
    root = calc.build()
    for f in _walk(root):
        if getattr(f, "key", None) in ("count-son", "count-daughter"):
            assert f.expand is True


async def test_tree_card_is_titled_and_branches_align_to_the_top():
    """ft.Row centres its children vertically by default, so a branch holding fewer
    chips floated up and its category heading landed on a different line from its
    neighbours'. The tree card also needed a title and divider like the other two."""
    calc, pg, loc = await _page()
    calc.heirs = {"wife": 1, "son": 2, "daughter": 1, "brother_full": 1}
    calc.estate = estate_mod.Estate()
    calc._compute()
    root = calc.build()

    tree = next(
        c for c in _walk(root)
        if isinstance(c, ft.Card)
        and any(
            isinstance(x, ft.Text) and x.value == loc.get("calc.tree")
            for x in _walk(c)
        )
    )
    col = tree.content.content
    head = col.controls[0]
    assert head.size == 15
    assert head.weight == ft.FontWeight.BOLD
    assert isinstance(col.controls[1], ft.Divider)

    branch_rows = [
        c for c in col.controls
        if isinstance(c, ft.Row)
        and any(isinstance(x, ft.Column) for x in c.controls)
    ]
    assert len(branch_rows) == 1
    assert branch_rows[0].vertical_alignment == ft.CrossAxisAlignment.START


async def test_parents_stay_paired_on_a_phone_but_count_fields_stack():
    """A parent row is a checkbox and a short label; a count field is a 150px label
    plus an entry. They must not share one threshold, or the parents stack on a
    phone where they plainly fit side by side."""
    from app.pages.calculate import MIN_CHECKBOX_WIDTH, MIN_FIELD_WIDTH

    async def _cols(width):
        calc, pg, _ = await _page(width=width)
        root = calc.build()
        rows = [
            r for r in _walk(root)
            if isinstance(r, ft.ResponsiveRow)
            and "father" in {x.key for x in _walk(r) if isinstance(getattr(x, "key", None), str)}
        ]
        inner = min(rows, key=lambda r: sum(1 for _ in _walk(r)))
        parent_row = inner
        sons = [
            r for r in _walk(root)
            if isinstance(r, ft.ResponsiveRow)
            and "count-son" in {x.key for x in _walk(r) if isinstance(getattr(x, "key", None), str)}
        ]
        son_row = min(sons, key=lambda r: sum(1 for _ in _walk(r)))
        return (
            sorted({c.col for c in parent_row.controls}),
            sorted({c.col for c in son_row.controls}),
        )

    # a typical phone: parents fit, counts do not
    for width in (360, 390, 430):
        parents, sons = await _cols(width)
        assert parents == [6], f"parents stacked at {width}px"
        assert sons == [12], f"counts should stack at {width}px"

    # a wide pane pairs both
    assert await _cols(1167) == ([6], [6])

    # the two thresholds must actually differ, or this test proves nothing
    assert MIN_CHECKBOX_WIDTH < 150 + MIN_FIELD_WIDTH


async def test_wife_count_sits_beside_the_radios_until_the_pane_is_too_narrow():
    """A `wrap=True` row is the wrong tool: a wrapping child greedily takes the full
    pane width, so the dropdown dropped underneath at every size. The pane decides."""
    from app.pages.calculate import MIN_SPOUSE_INLINE_WIDTH

    async def _section(width):
        calc, pg, loc = await _page(width=width)
        root = calc.build()
        spouse = next(
            c for c in _walk(root)
            if isinstance(c, ft.Column)
            and getattr(c.controls[0], "value", None) == loc.get("calc.spouse")
        )
        return spouse, calc._form_pane_width()

    # side by side wherever they genuinely fit
    for width in (992, 1100, 1167, 1280, 1600):
        section, pane = await _section(width)
        assert isinstance(section.controls[1], ft.Row), f"dropdown dropped at {width}px (pane {pane:.0f})"
        assert [type(x).__name__ for x in section.controls[1].controls] == [
            "RadioGroup",
            "Dropdown",
        ]

    # underneath on a phone, as two siblings, so it is never cut off the screen
    for width in (360, 390, 430):
        section, pane = await _section(width)
        assert not isinstance(section.controls[1], ft.Row), f"crowded at {width}px (pane {pane:.0f})"
        assert [type(x).__name__ for x in section.controls[1:3]] == [
            "RadioGroup",
            "Dropdown",
        ]

    # the radios wrap in both layouts, so a misjudged threshold can never overflow
    for width in (360, 1167):
        section, _ = await _section(width)
        group = next(c for c in _walk(section) if isinstance(c, ft.RadioGroup))
        assert group.content.wrap is True
        assert _by_key(section, "count-wife") is not None

    # the threshold has to sit between a phone and the narrowest two-pane layout
    _, pane992 = await _section(992)
    _, pane430 = await _section(430)
    assert pane430 < MIN_SPOUSE_INLINE_WIDTH <= pane992


async def test_every_result_pane_block_shares_one_16px_inset():
    """The estate arithmetic line ran to the bezel while the table above it was
    inset. Every block in the result pane has to start on the same left edge."""
    calc, pg, _ = await _page()
    calc.heirs = {"wife": 1, "son": 2}
    calc.estate = estate_mod.Estate(gross=1_000_000)
    calc._compute()
    root = calc.build()

    # result_card is the only Column whose key is not a string; its single child is
    # the block list built by _build_result()
    host = next(
        c for c in _walk(root)
        if isinstance(c, ft.Column)
        and getattr(c, "key", None) is not None
        and not isinstance(c.key, str)
    )
    result = host.controls[0]

    def _inset(block):
        node = block.content if isinstance(block, ft.Card) else block
        p = getattr(node, "padding", None)
        if isinstance(p, (int, float)):
            return (p, p)
        return (getattr(p, "left", None), getattr(p, "right", None))

    # tree, table, breakdown, notes, details
    assert len(result.controls) == 5
    for block in result.controls:
        assert _inset(block) == (16, 16), f"{type(block).__name__} is not inset"


async def test_heir_card_reads_as_four_titled_sections():
    """The card groups spouse/children/parents/siblings, so the grouping has to be
    visible: separated by spacing, with headings that carry weight."""
    calc, pg, loc = await _page()
    root = calc.build()

    card = next(
        c for c in _walk(root)
        if isinstance(c, ft.Card)
        and any(isinstance(x, ft.Text) and x.value == loc.get("calc.heirs")
                for x in _walk(c))
    )
    assert getattr(card.content, "padding", None) == 16
    col = card.content.content
    assert getattr(col, "spacing", None) == 16, "sections must be visually separated"

    headings = [c.controls[0] for c in col.controls if isinstance(c, ft.Column)]
    titles = [h.value for h in headings]
    assert titles == [
        loc.get("calc.spouse"),
        loc.get("calc.children"),
        loc.get("calc.parents"),
        loc.get("calc.siblings"),
    ]
    for h in headings:
        assert h.size == 13
        assert h.weight == ft.FontWeight.BOLD

    # a single divider separates the card title from the first section
    assert sum(isinstance(c, ft.Divider) for c in col.controls) == 1
    assert isinstance(col.controls[1], ft.Divider)

    # presentation only: every field is still there
    keys = {getattr(x, "key", None) for x in _walk(card)} - {None}
    for k in ("count-son", "count-daughter", "count-wife", "father", "mother",
              "count-brother_full", "count-sister_uterine"):
        assert k in keys, f"{k} disappeared from the heir card"
    assert _by_key(root, "count-wife") is not None

    # the wife count sits beside the choice that enables it, not under it
    spouse = next(
        s for s in col.controls
        if isinstance(s, ft.Column) and s.controls[0].value == loc.get("calc.spouse")
    )
    body = spouse.controls[1]
    assert isinstance(body, ft.Row)
    assert [type(x).__name__ for x in body.controls] == ["RadioGroup", "Dropdown"]
    assert _by_key(body, "count-wife") is not None


async def test_result_table_cells_carry_tooltips():
    """Amounts are no_wrap + ellipsis, so every cell keeps its full value in a
    tooltip for narrow panes."""
    calc, pg, _ = await _page()
    calc.heirs = {"son": 1}
    calc.estate = estate_mod.Estate()
    calc._compute()
    root = calc.build()
    table = _by_key(root, "result-table")
    assert table is not None
    cells = [c for c in _walk(table) if isinstance(c, ft.Text) and c.expand]
    assert cells
    for cell in cells:
        assert cell.no_wrap is True
        assert cell.overflow == ft.TextOverflow.ELLIPSIS
        assert cell.tooltip == cell.value


def test_equivalence_lines_use_group_share_so_sum_to_one():
    from app.calculation.engine import Row
    from app.pages.calculate import _equivalence_lines
    rows = [
        Row(key="son", count=2, share=F(1, 5)),     # per person
        Row(key="daughter", count=1, share=F(1, 5)),
    ]
    lines = _equivalence_lines(rows)
    # group shares: 2/5 and 1/5 -> lcm 5 -> "2/5 = 2/5", "1/5 = 1/5"
    assert lines == ["2/5 = 2/5", "1/5 = 1/5"]


async def test_result_card_uses_scroll_key_so_scroll_to_can_find_it():
    calc, pg, _ = await _page()
    calc.build()
    key = calc.result_card.key
    assert isinstance(key, ft.ScrollKey)
    assert str(key) == "result-card"


async def test_wife_count_is_a_dropdown_limited_to_one_through_four():
    calc, pg, _ = await _page()
    calc.build()
    wife = calc._wife_count
    assert isinstance(wife, ft.Dropdown)
    assert [o.key for o in wife.options] == ["1", "2", "3", "4"]
    assert wife.value == "1"
    assert wife.editable is not True


async def test_wife_count_dropdown_feeds_slot_and_defaults_to_one():
    calc, pg, _ = await _page()
    calc.build()
    calc._spouse.value = "wife"
    calc._sync_wife_count()
    assert calc._wife_count.disabled is False
    assert calc._slot_from_inputs() == {"wife": 1}
    calc._wife_count.value = "4"
    assert calc._slot_from_inputs() == {"wife": 4}
    calc._spouse.value = "none"
    calc._sync_wife_count()
    assert calc._wife_count.disabled is True
    assert "wife" not in calc._slot_from_inputs()


async def test_wife_count_empty_or_zero_falls_back_to_one():
    calc, pg, _ = await _page()
    calc.build()
    calc._spouse.value = "wife"
    for bad in ("", "0", None):
        calc._wife_count.value = bad
        assert calc._slot_from_inputs() == {"wife": 1}


async def test_two_pane_mode_scrolls_form_and_results_independently():
    calc, pg, _ = await _page()
    pg.width = 1400
    root = calc.build()
    assert calc.two_pane is True
    assert root.scroll is None, "outer container must not scroll in two-pane mode"
    form = _by_key(root, "col-cards")
    result = _by_key(root, "pane-result")
    assert form is not None and result is not None
    assert form.scroll == ft.ScrollMode.AUTO
    assert result.scroll == ft.ScrollMode.AUTO


async def test_stacked_mode_scrolls_the_outer_container_only():
    calc, pg, _ = await _page()
    pg.width = 800
    root = calc.build()
    assert calc.two_pane is False
    assert root.scroll == ft.ScrollMode.AUTO
    assert _by_key(root, "col-cards").scroll is None
    assert _by_key(root, "pane-result").scroll is None


async def test_two_pane_mode_keeps_the_result_scroll_key_and_scroll_host():
    calc, pg, _ = await _page()
    pg.width = 1400
    root = calc.build()
    assert isinstance(calc.result_card.key, ft.ScrollKey)
    assert str(calc.result_card.key) == "result-card"
    assert calc._scroll_host is _by_key(root, "pane-result")
    assert _by_key(root, "btn-calculate") is not None
    assert _by_key(root, "back-home") is not None


async def test_stacked_mode_scroll_host_is_the_root_container():
    calc, pg, _ = await _page()
    pg.width = 800
    root = calc.build()
    assert calc._scroll_host is root
    assert calc._scroll_host is not _by_key(root, "pane-result")


async def test_is_two_pane_treats_unset_width_as_stacked():
    assert is_two_pane(None) is False
    assert is_two_pane(0) is False
    assert is_two_pane(991) is False
    assert is_two_pane(992) is True
    assert is_two_pane(1400) is True


def _texts(root):
    out = []
    stack = [root]
    while stack:
        node = stack.pop()
        if isinstance(node, ft.Text) and isinstance(node.value, str):
            out.append(node.value)
        stack.extend(getattr(node, "controls", []) or [])
        content = getattr(node, "content", None)
        if content is not None:
            stack.append(content)
        # ExpansionTile keeps its header in `title`, not `controls`/`content`
        title = getattr(node, "title", None)
        if isinstance(title, ft.Control):
            stack.append(title)
    return out


def test_empty_result_shows_shells_with_hint():
    page = FakePage()
    loc = Localization("en", None)
    calc = CalculationPage(page, loc, back_home=lambda: None)
    calc.build()
    calc._collect()
    calc._compute()
    text = " ".join(_texts(calc._build_result()))
    assert loc.get("calc.empty_hint") in text
    assert loc.get("calc.tree") in text
    assert loc.get("calc.details") in text
    for header in (loc.get("calc.col_heir"), loc.get("calc.col_share"), loc.get("calc.col_total")):
        assert header in text


def test_empty_result_hint_is_indonesian_in_id():
    page = FakePage()
    loc = Localization("id", None)
    calc = CalculationPage(page, loc, back_home=lambda: None)
    calc.build()
    calc._collect()
    calc._compute()
    text = " ".join(_texts(calc._build_result()))
    assert "Jalankan perhitungan untuk melihat hasil di sini." in text