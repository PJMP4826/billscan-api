from src.domain.ports.repositories.reporting_repository_port import (
    ReportingRepositoryPort,
)
from src.application.dtos.cfdi import CfdiListResponse
from src.domain.value_objects.user_id import UserId


class GetCfdiListUseCase:
    def __init__(self, reporting_repository: ReportingRepositoryPort) -> None:
        self._reporting_repository = reporting_repository

    async def execute(
        self, user_id: UserId, page: int = 1, page_size: int = 20
    ) -> CfdiListResponse:
        return await self._reporting_repository.get_cfdi_list(
            user_id.value, page, page_size
        )
