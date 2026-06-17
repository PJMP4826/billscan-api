from abc import ABC, abstractmethod
from typing import Any


class ReceiptJobDetailsRepositoryPort(ABC):
    @abstractmethod
    async def create(self, user_id: str, job_name: str) -> int:
        pass

    @abstractmethod
    async def mark_extracting(self, job_id: int) -> None:
        pass

    @abstractmethod
    async def mark_completed(self, job_id: int, receipt_id: int) -> None:
        pass

    @abstractmethod
    async def mark_failed(self, job_id: int, error_message: str) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, job_id: int) -> dict[str, Any] | None:
        pass

    @abstractmethod
    async def find_by_user_id(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def find_by_user_id_with_images(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def find_pending(self, limit: int = 100) -> list[dict[str, Any]]:
        pass
