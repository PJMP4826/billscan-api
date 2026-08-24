from typing import Literal
from typing import Any
from src.domain.ports.file_storage_port import FileStoragePort
from src.domain.ports.repositories.reporting_repository_port import (
    ReportingRepositoryPort,
)


class GetReceiptDetailUseCase:
    def __init__(
        self,
        file_storage: FileStoragePort,
        reporting_repository: ReportingRepositoryPort,
    ) -> None:
        self._file_storage = file_storage
        self._reporting_repository = reporting_repository

    async def execute(
        self, receipt_uuid: str, detail_level: Literal["base", "full"] = "base"
    ) -> dict[str, Any | None]:
        if detail_level == "full":
            return await self._reporting_repository.get_receipt_full_detail(
                receipt_uuid=receipt_uuid,
            )

        rows = await self._reporting_repository.get_receipt_base_detail(
            receipt_uuid=receipt_uuid,
        )

        if file_key := rows.pop("file_key", None):
            file_url = await self._file_storage.get_url(str(file_key))
            rows["file_url"] = file_url

        return rows
