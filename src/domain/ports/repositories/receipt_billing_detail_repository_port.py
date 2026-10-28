from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from src.domain.value_objects.billing_data import BillingData


class ReceiptBillingDetailRepositoryPort(ABC):
    @abstractmethod
    async def insert(self, receipt_id: int, billing: BillingData | None) -> None:
        pass

    @abstractmethod
    async def find_by_receipt_id(self, receipt_id: int) -> dict[str, Any] | None:
        pass

    @abstractmethod
    async def set_billing_preferences(
        self,
        receipt_id: int,
        uso_cfdi: str | None = None,
        regimen_code: str | None = None,
    ) -> None:
        """Guarda la elección fiscal (uso de CFDI y régimen) enviada por el cliente.

        Los valores ``None`` no sobrescriben lo ya persistido.
        """
        pass

    @abstractmethod
    async def update_billing_status(
        self,
        receipt_id: int,
        billing_status: str,
        facturagpt_session_id: str | None = None,
        billing_error_code: str | None = None,
        billing_error_message: str | None = None,
        cfdi_content: dict[str, Any] | None = None,
        completed_at: str | datetime | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def delete_by_receipt_id(self, receipt_id: int) -> None:
        pass
