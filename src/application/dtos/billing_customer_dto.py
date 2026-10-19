from dataclasses import dataclass
from src.domain.enums.tax_regime import TaxRegime


@dataclass
class BillingCustomerInfoDto:
    """Fiscal identity of the invoice recipient."""

    razon_social: str
    rfc: str
    email: str
    regimen: TaxRegime  # SAT régimen fiscal code e.g. "601"
    cp: str
    address: str | None = None
