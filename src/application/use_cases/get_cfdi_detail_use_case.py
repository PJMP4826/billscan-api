from typing import Any

from src.domain.ports.file_storage_port import FileStoragePort
from src.domain.ports.repositories.reporting_repository_port import (
    ReportingRepositoryPort,
)
from src.domain.value_objects.user_id import UserId


class GetCfdiDetailUseCase:
    def __init__(
        self,
        file_storage: FileStoragePort,
        reporting_repository: ReportingRepositoryPort,
    ) -> None:
        self._file_storage = file_storage
        self._reporting_repository = reporting_repository

    async def execute(self, user_id: UserId, receipt_uuid: str) -> dict[str, Any | None]:
        row = await self._reporting_repository.get_cfdi_detail(
            user_id=user_id.value, receipt_uuid=receipt_uuid
        )

        xml_key = row.invoice.xml_url
        pdf_key = row.invoice.pdf_url

        return {
            "receipt_uuid": row.receipt_uuid,
            "cfdi": row.cfdi.to_dict(),
            "xml_url": (
                await self._file_storage.get_url(str(xml_key)) if xml_key else None
            ),
            "pdf_url": (
                await self._file_storage.get_url(str(pdf_key)) if pdf_key else None
            ),
        }
