from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class CfdiListItem:
    """Proyección ligera de un CFDI emitido, extraída del JSONB
    `cfdi_summary` sin hidratar el CfdiDto completo."""

    receipt_uuid: str
    emisor_nombre: str
    total: Decimal
    serie: str | None = None
    folio: str | None = None
    uso_cfdi: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_uuid": self.receipt_uuid,
            "emisor_nombre": self.emisor_nombre,
            "total": str(self.total),
            "serie": self.serie,
            "folio": self.folio,
            "uso_cfdi": self.uso_cfdi,
        }
