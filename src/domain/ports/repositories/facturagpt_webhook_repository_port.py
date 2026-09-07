from abc import ABC, abstractmethod
from typing import Any


class FacturaGPTWebhookRepositoryPort(ABC):
    """
    Puerto de `facturagpt_webhooks` (idempotencia de webhooks de FacturaGPT,
    PK = idempotency_key).

    Semántica de columnas:
    - `received_at`: cuándo se almacenó el evento (store-before-process).
    - `processed_at`: NULL mientras el evento no se haya procesado
      correctamente. El worker lo setea al terminar con éxito; si falla,
      queda NULL y un reintento (red de FacturaGPT o job de reconciliación)
      puede volver a procesarlo sin duplicar efecto.
    """

    @abstractmethod
    async def insert_if_new(
        self,
        idempotency_key: str,
        event_type: str,
        session_id: str,
        payload: dict[str, Any],
    ) -> bool:
        """
        Inserta el evento crudo si la idempotency_key no existe.

        Returns:
            True -> evento nuevo (el caller debe encolarlo).
            False -> duplicado (reintento de red; el caller NO debe reprocesar).
        """
        pass

    @abstractmethod
    async def find_by_key(self, idempotency_key: str) -> dict[str, Any] | None:
        """Devuelve la fila cruda (incluye `payload`, `processed_at`)."""
        pass

    @abstractmethod
    async def find_by_session_id(self, session_id: str) -> list[dict[str, Any]]:
        """Devuelve todos los eventos recibidos para una sesión de FacturaGPT."""
        pass

    @abstractmethod
    async def mark_processed(self, idempotency_key: str) -> bool:
        """
        Marca el evento como procesado (setea `processed_at = NOW()`) SOLO si
        aún no lo estaba (UPDATE condicional).

        Returns:
            True -> el worker de esta corrida ganó el marcado.
            False -> otro worker ya lo procesó (skip idempotente).
        """
        pass

    @abstractmethod
    async def update_error(
        self, idempotency_key: str, error_message: str | None
    ) -> None:
        """
        Registra el error del worker dejando `processed_at` en NULL para
        permitir un reintento posterior.
        """
        pass
