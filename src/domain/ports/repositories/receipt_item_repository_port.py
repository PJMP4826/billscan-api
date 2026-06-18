from abc import ABC, abstractmethod
from typing import Any
from src.domain.value_objects.line_item import LineItem

class ReceiptItemRepositoryPort(ABC):
    @abstractmethod
    async def insert(self, receipt_id: int, item: LineItem) -> int:
        pass

    @abstractmethod
    async def insert_many(self, receipt_id: int, items: list[LineItem]) -> list[int]:
        pass

    @abstractmethod
    async def find_by_receipt_id(self, receipt_id: int) -> list[dict[str, Any]]:
        pass
        
    @abstractmethod
    async def delete_by_receipt_id(self, receipt_id: int) -> None:
        pass