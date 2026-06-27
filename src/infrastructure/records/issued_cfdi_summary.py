from decimal import Decimal
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class IssuedCFDISummary:
    total_facturado: Decimal
    facturas_generadas: int

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
