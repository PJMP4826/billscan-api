from src.domain.ports.repositories.reporting_repository_port import (
    ReportingRepositoryPort,
)
from src.application.dtos.recent_activity_item_dto import RecentActivityItem


class GetRecentActivityUseCase:
    def __init__(self, reporting_repository: ReportingRepositoryPort) -> None:
        self._reporting_repository = reporting_repository

    async def execute(
        self,
        receipt_uuid: str | None = None,
        status_filter: str | None = None,
        limit: int = 10,
    ) -> list[RecentActivityItem]:
        return await self._reporting_repository.get_recent_activity(
            receipt_uuid=receipt_uuid,
            status_filter=status_filter,
            limit=limit,
        )
