from . import engine, heirs
from . import estate as estate_mod


class CalculationState:
    """Domain state for one calculate screen.

    Plain data in, plain data out — no Flet imports, no controls. The page
    parses its text fields into a slots dict and an Estate and hands them to
    collect(); ui builders read the stored data to render. A structural test
    pins the no-flet rule.
    """

    def __init__(self):
        self.heirs: dict[str, int] = {}
        self.estate = estate_mod.Estate()
        self.result: engine.Result | None = None

    def collect(self, slots: dict[str, int], estate: estate_mod.Estate) -> None:
        self.heirs = heirs.normalize(slots)
        self.estate = estate

    def compute(self) -> None:
        self.result = engine.resolve(
            self.heirs,
            estate=self.estate if self.estate.has_numbers else None,
        )
