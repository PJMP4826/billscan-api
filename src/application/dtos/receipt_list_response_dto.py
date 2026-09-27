from typing import Any
from dataclasses import dataclass

from src.application.dtos.receipt_list_item_dto import (
    ReceiptListItemData,
    ReceiptListItemResponse,
)


@dataclass(frozen=True)
class ReceiptListData:
    items: list[ReceiptListItemData]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class ReceiptListResponse:
    items: list[ReceiptListItemResponse]
    total: int
    page: int
    page_size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipts": [item.to_dict() for item in self.items],
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": -(-self.total // self.page_size) if self.page_size else 0,
        }
