from decimal import Decimal
from dataclasses import dataclass


@dataclass(frozen=True)
class CompletedBillingSummary:
    total_billed: Decimal
    invoices_generated: int
    period: str

    def to_dict(self) -> dict[str, str]:
        return {
            "total_facturado": str(self.total_billed),
            "facturas_generadas": str(self.invoices_generated),
            "periodo": self.period,
        }
