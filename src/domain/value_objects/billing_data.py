from dataclasses import dataclass
from typing import Optional
from datetime import date

@dataclass(frozen=True)
class BillingData:
    is_billable: bool = False
    has_qr_code: bool = False
    billing_url: Optional[str] = None
    billing_code: Optional[str] = None
    barcode: Optional[str] = None
    expiration_date: Optional[date] = None
    billing_metadata: dict[str, str] | None = None

    def __post_init__(self) -> None:
        # if self.has_qr_code and not self.billing_url:
        #     raise ValueError("When has_qr_code=True, billing_url must be provided.")
        if self.is_billable:
            if not any([self.billing_url, self.billing_code, self.barcode]):
                raise ValueError(
                    "When is_billable=True, at least one of billing_url, "
                    "billing_code, or barcode must be provided."
                )
            
    @property
    def is_expired(self) -> bool:
        if not self.expiration_date:
            return False
        return self.expiration_date < date.today()
