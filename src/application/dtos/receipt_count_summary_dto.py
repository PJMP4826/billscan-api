from decimal import Decimal
from dataclasses import dataclass


@dataclass(frozen=True)
class ReceiptCountSummary:
    total: int
    billable: int
    non_billable: int
    total_spent: Decimal

    def to_dict(self) -> dict[str, str]:
        return {
            "total": str(self.total),
            "facturables": str(self.billable),
            "no_facturables": str(self.non_billable),
            "total_gastado": str(self.total_spent),
        }
