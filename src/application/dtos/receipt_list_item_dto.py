from decimal import Decimal
from dataclasses import dataclass

from src.domain.enums.billing_status import BillingStatus


@dataclass(frozen=True)
class ReceiptListItemData:
    receipt_uuid: str
    merchant_name: str | None
    registered_at: str
    total: Decimal
    status: BillingStatus
    file_key: str

@dataclass(frozen=True)
class ReceiptListItemResponse:
    receipt_uuid: str
    merchant_name: str | None
    registered_at: str
    total: Decimal
    status: BillingStatus
    file_url: str  

    def to_dict(self) -> dict[str, str]:
        return {
            "receipt_uuid": self.receipt_uuid,
            "nombre_comercio": self.merchant_name or "Sin comercio",
            "fecha_registro": self.registered_at,
            "total": str(self.total),
            "estado": self.status.value,
            "file_url": self.file_url
        }