from decimal import Decimal
from dataclasses import dataclass


@dataclass(frozen=True)
class DeductibleExpenseSummary:
    total_posibles_gastos_deducibles: Decimal
    receipts_por_procesar: int

    def to_dict(self) -> dict[str, str]:
        return {
            "total_posibles_gastos_deducibles": str(self.total_posibles_gastos_deducibles),
            "receipts_por_procesar": str(self.receipts_por_procesar)
        }
