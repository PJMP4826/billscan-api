from abc import ABC, abstractmethod
from typing import Any
from src.domain.value_objects.tax_detail import TaxDetail


class ReceiptTaxRepositoryPort(ABC):
    @abstractmethod
    async def insert(self, receipt_id: int, tax: TaxDetail) -> int:
        pass

    @abstractmethod
    async def insert_many(self, receipt_id: int, taxes: list[TaxDetail]) -> list[int]:
        pass

    @abstractmethod
    async def find_by_receipt_id(self, receipt_id: int) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def delete_by_receipt_id(self, receipt_id: int) -> None:
        pass
