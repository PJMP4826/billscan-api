from abc import ABC, abstractmethod
from typing import Any


class BillingFileRepositoryPort(ABC):
    """
    Puerto de `billing_files` (XML/PDF de factura ya generados, 1:M por
    receipt). Poblado por el worker de webhooks cuando FacturaGPT entrega
    la factura; su existencia además alimenta el reporte de CFDIs emitidos.
    """

    @abstractmethod
    async def insert(
        self,
        receipt_id: int,
        file_type: str | None,
        file_key: str,
        mime_type: str | None = None,
    ) -> int:
        """Inserta la referencia a un archivo de factura y devuelve su id."""
        pass

    @abstractmethod
    async def find_by_receipt_id(self, receipt_id: int) -> list[dict[str, Any]]:
        """Devuelve los archivos de factura de un receipt (ordenados por id)."""
        pass

    @abstractmethod
    async def delete_by_receipt_id(self, receipt_id: int) -> None:
        """Elimina los archivos de factura de un receipt."""
        pass
