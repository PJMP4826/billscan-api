from typing import Any
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

from src.domain.ports.file_storage_port import FileStoragePort
from src.domain.ports.repositories.receipt_image_repository_port import (
    ReceiptImageRepositoryPort,
)
from src.domain.ports.repositories.receipt_repository_port import (
    ReceiptRepositoryPort,
)


class GetReceiptDetailUseCase:
    def __init__(
        self,
        file_storage: FileStoragePort,
        receipt_repository: ReceiptRepositoryPort,
        receipt_image_repository: ReceiptImageRepositoryPort,
    ) -> None:
        self._file_storage = file_storage
        self._receipt_repository = receipt_repository
        self._receipt_image_repository = receipt_image_repository

    async def execute(self, receipt_uuid: str) -> dict[str, Any | None]:
        receipt = await self._receipt_repository.find_by_uuid(receipt_uuid)

        data = self._json_safe(receipt.to_dict())
        file_key = await self._receipt_image_repository.find_key_by_receipt_uuid(
            receipt_uuid=receipt.receipt_uuid
        )
        file_url = await self._file_storage.get_url(str(file_key))

        data.update({"file_url": file_url})

        return data

    def _json_safe(self, value: Any) -> Any:
            """Convierte valores no serializables por json a tipos JSON-safe."""
            if isinstance(value, Enum):
                return self._json_safe(value.value)
            if isinstance(value, Decimal):
                return str(value)
            if isinstance(value, (datetime, date, time)):
                return value.isoformat()
            if isinstance(value, dict):
                return {key: self._json_safe(item) for key, item in value.items()} # type: ignore
            if isinstance(value, (list, tuple)):
                return [self._json_safe(item) for item in value] # type: ignore
            return value
