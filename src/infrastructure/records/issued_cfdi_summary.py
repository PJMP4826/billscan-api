from decimal import Decimal
from dataclasses import dataclass


@dataclass(frozen=True)
class IssuedCFDISummary:
    total_facturado: Decimal
    facturas_generadas: int

    def to_dict(self) -> dict[str, str]:
        return {
            "total_facturado": str(self.total_facturado),
            "facturas_generadas": str(self.facturas_generadas),
        }
