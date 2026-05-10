from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MerchantData:
    name: str
    tax_id: Optional[str] = None
    address: Optional[str] = None
    branch_id: Optional[str] = None
    phone: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Merchant name must not be empty.")
        if self.tax_id is not None and not self.tax_id.strip():
            raise ValueError("tax_id must not be an empty string.")
