from decimal import Decimal
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class DeductibleExpenseSummary:
    total_posibles_gastos_deducibles: Decimal
    receipts_por_procesar: int

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
