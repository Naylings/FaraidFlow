from dataclasses import dataclass


@dataclass
class Estate:
    gross: int = 0
    funeral: int = 0
    debts: int = 0
    wasiat: int = 0

    @property
    def has_numbers(self) -> bool:
        return self.gross > 0

    def _cap_base(self) -> int:
        return self.gross - self.funeral - self.debts

    @property
    def unpaid(self) -> int:
        return max(0, self.debts - (self.gross - self.funeral))

    @property
    def wasiat_cap(self) -> int:
        base = self._cap_base()
        return max(0, base // 3)

    @property
    def wasiat_excess(self) -> int:
        return max(0, self.wasiat - self.wasiat_cap)

    @property
    def wasiat_ok(self) -> bool:
        base = self._cap_base()
        if base <= 0:
            return self.wasiat == 0
        return self.wasiat * 3 <= base

    @property
    def net(self) -> int:
        return max(0, self._cap_base() - self.wasiat)