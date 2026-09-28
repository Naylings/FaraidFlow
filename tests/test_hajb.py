from app.calculation.hajb import surviving


def test_son_blocks_all_siblings():
    got = surviving({"son": 1, "sister_full": 1, "sister_consang": 1, "sister_uterine": 1})
    assert got["sister_full"] == 0
    assert got["sister_consang"] == 0
    assert got["sister_uterine"] == 0


def test_daughter_does_not_block_full_or_consang():
    got = surviving({"daughter": 1, "sister_full": 1, "sister_consang": 1})
    assert got["sister_full"] == 1
    assert got["sister_consang"] == 1


def test_daughter_blocks_uterine():
    got = surviving({"daughter": 1, "sister_uterine": 1})
    assert got["sister_uterine"] == 0


def test_father_blocks_all_siblings():
    got = surviving({"father": 1, "sister_uterine": 2, "brother_full": 1})
    assert got["sister_uterine"] == 0
    assert got["brother_full"] == 0


def test_full_brother_blocks_consang_only():
    got = surviving({"brother_full": 1, "brother_consang": 1, "sister_full": 1})
    assert got["brother_full"] == 1
    assert got["sister_full"] == 1
    assert got["brother_consang"] == 0


def test_no_blockers_keeps_everything():
    got = surviving({"sister_consang": 1, "sister_uterine": 1, "mother": 1})
    assert got["sister_consang"] == 1
    assert got["sister_uterine"] == 1
    assert got["mother"] == 1