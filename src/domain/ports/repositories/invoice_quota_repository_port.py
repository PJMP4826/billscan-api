from abc import ABC, abstractmethod


class InvoiceQuotaRepositoryPort(ABC):
    """Contrato para el consumo atómico de la cuota de facturas por RFC."""

    @abstractmethod
    async def try_reserve(
        self, receipt_id: int, rfc_hash: str, max_invoices: int
    ) -> bool:
        """Reserva cupo para un receipt.

        Es idempotente por ``receipt_id``: reintentar el mismo ticket no
        consume cupo adicional. Devuelve ``False`` si ya se alcanzó el límite.
        """
        pass

    @abstractmethod
    async def release(self, receipt_id: int) -> None:
        """Devuelve el cupo de un intento fallido."""
        pass

    @abstractmethod
    async def mark_consumed(self, receipt_id: int) -> None:
        """Marca la factura como timbrada (``COMPLETED``)."""
        pass

    @abstractmethod
    async def count_in_use(self, rfc_hash: str) -> int:
        """Cuenta las facturas reservadas o consumidas de un RFC."""
        pass
