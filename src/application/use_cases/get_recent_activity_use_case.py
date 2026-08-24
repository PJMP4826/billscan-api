from decimal import Decimal

from src.domain.ports.file_storage_port import FileStoragePort
from src.domain.ports.repositories.reporting_repository_port import (
    ReportingRepositoryPort,
)
from src.application.dtos.recent_activity_item_dto import RecentActivityItem


class GetRecentActivityUseCase:
    def __init__(
        self,
        file_storage: FileStoragePort,
        reporting_repository: ReportingRepositoryPort,
    ) -> None:
        self._file_storage = file_storage
        self._reporting_repository = reporting_repository

    async def execute(
        self,
        receipt_uuid: str | None = None,
        status_filter: str | None = None,
        limit: int = 10,
    ) -> list[RecentActivityItem]:

        rows = await self._reporting_repository.get_recent_activity(
            receipt_uuid=receipt_uuid,
            status_filter=status_filter,
            limit=limit,
        )

        recent_activity_item: list[RecentActivityItem] = []
        for row in rows:
            file_url = await self._file_storage.get_url(row["file_key"])
            recent_activity_item.append(
                RecentActivityItem(
                    comercio=row["comercio"],
                    file_url=file_url,
                    fecha_alta=str(row["fecha_alta"]),
                    total=Decimal(str(row["total"])),
                    status=row["status"],
                )
            )

        return recent_activity_item
