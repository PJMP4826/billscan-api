from abc import ABC, abstractmethod
from typing import Any


class ReceiptImageRepositoryPort(ABC):
    @abstractmethod
    async def insert(
        self,
        receipt_job_id: int,
        file_key: str,
        file_url: str,
        mime_type: str = "image/jpeg",
        page_number: int = 1,
        receipt_id: int | None = None,
    ) -> int:
        """Inserta una imagen ligada a un job.

        Retorna el ID de la imagen insertada.
        """
        pass

    @abstractmethod
    async def insert_many(
        self, receipt_job_id: int, images: list[dict[str, Any]]
    ) -> list[int]:
        """Inserta varias imágenes (multi-página) ligadas a un job.

        Cada elemento de `images` debe tener las claves: file_key,
        file_url, y opcionalmente mime_type, page_number.
        """
        pass

    @abstractmethod
    async def backfill_receipt_id(self, receipt_job_id: int, receipt_id: int) -> None:
        """Actualiza receipt_id en todas las imágenes de un job, una vez
        que el Receipt fue creado con éxito."""
        pass

    @abstractmethod
    async def find_by_receipt_id(self, receipt_id: int) -> list[dict[str, Any]]:
        """Recupera todas las imágenes asociadas a un receipt_id."""
        pass

    @abstractmethod
    async def find_by_job_id(self, receipt_job_id: int) -> list[dict[str, Any]]:
        """Recupera todas las imágenes asociadas a un receipt_job_id antes

        de que exista el receipt_id.
        """
        pass

    @abstractmethod
    async def delete_by_receipt_id(self, receipt_id: int) -> None:
        """Elimina todas las imágenes asociadas a un receipt_id."""
        pass

    @abstractmethod
    async def delete_by_job_id(self, receipt_job_id: int) -> None:
        """Elimina todas las imágenes asociadas a un receipt_job_id."""
        pass
