from decimal import Decimal
from dataclasses import dataclass


@dataclass(frozen=True)
class DeductibleExpenseSummary:
    total_posibles_gastos_deducibles: Decimal
    receipts_por_procesar: int
