import ast
from pathlib import Path

from app.calculation import estate as estate_mod
from app.calculation.state import CalculationState

STATE_FILE = Path(__file__).resolve().parents[1] / "src" / "app" / "calculation" / "state.py"


def test_state_collect_compute_roundtrip():
    s = CalculationState()
    s.collect({"husband": 1}, estate_mod.Estate(gross=1000000))
    assert s.heirs.get("husband") == 1
    assert s.estate.gross == 1000000
    s.compute()
    assert s.result is not None
    assert s.result.rows, "a sole husband with an estate must produce rows"


def test_state_imports_no_flet():
    tree = ast.parse(STATE_FILE.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    assert "flet" not in imports, "state.py must stay UI-free"
