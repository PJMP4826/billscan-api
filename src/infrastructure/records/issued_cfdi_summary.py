from decimal import Decimal
from dataclasses import dataclass


@dataclass(frozen=True)
class IssuedCFDISummary:
    total_facturado: Decimal
    facturas_generadas: int
