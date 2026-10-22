from dataclasses import dataclass
from datetime import datetime
from src.domain.enums.tax_regime import TaxRegime


@dataclass(frozen=True)
class BillingCustomerRegimeDto:
    code: TaxRegime
    fecha_alta_sat: datetime | None = None

    @property
    def description(self) -> str:
        return self.code.description