from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BillingData:
    is_billable: bool
    has_qr_code: bool = False
    billing_url: Optional[str] = None
    billing_code: Optional[str] = None
    barcode: Optional[str] = None
    expiration_date: Optional[str] = None

    def __post_init__(self) -> None:
        if self.has_qr_code and not self.billing_url:
            raise ValueError("When has_qr_code=True, billing_url must be provided.")
        if self.is_billable:
            if not any([self.billing_url, self.billing_code, self.barcode]):
                raise ValueError(
                    "When is_billable=True, at least one of billing_url, "
                    "billing_code, or barcode must be provided."
                )
