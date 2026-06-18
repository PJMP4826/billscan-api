from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any


class ReceiptPaymentRepositoryPort(ABC):
    @abstractmethod
    async def insert(
        self,
        receipt_id: int,
        payment_method_code: str,
        amount: Decimal,
        card_last_four: str | None = None,
        authorization_code: str | None = None,
    ) -> int:
        pass

    @abstractmethod
    async def find_by_receipt_id(self, receipt_id: int) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def delete_by_receipt_id(self, receipt_id: int) -> None:
        pass
