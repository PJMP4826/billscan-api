from dataclasses import dataclass
from typing import Any

from src.application.dtos.cfdi.cfdi_list_item_dto import CfdiListItem


@dataclass(frozen=True)
class CfdiListResponse:
    items: list[CfdiListItem]
    total: int
    page: int
    page_size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "cfdis": [item.to_dict() for item in self.items],
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": -(-self.total // self.page_size) if self.page_size else 0,
        }
