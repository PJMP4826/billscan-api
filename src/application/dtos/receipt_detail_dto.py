from dataclasses import dataclass
from typing import Any

from src.domain.entities.receipt import Receipt
from src.shared.utils.json_safe_parse import json_safe


@dataclass(frozen=True)
class ReceiptDetailDto:
    """DTO de salida del caso de uso: la entidad de dominio `Receipt`
    ya hidratada más la presigned URL de su imagen.

    Mantiene los tipos del dominio (Decimal, Enum, datetime); la
    conversión a tipos JSON-safe es responsabilidad del controller.
    """

    receipt: Receipt
    file_url: str

    def to_dict(self) -> dict[str, Any]:
        data = json_safe(self.receipt.to_dict())
        data.update({"file_url": self.file_url})
        return data
