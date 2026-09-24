from src.domain.ports.repositories.reporting_repository_port import (
    ReportingRepositoryPort,
)
from src.application.dtos.cfdi import CfdiListResponse


class GetCfdiListUseCase:
    def __init__(self, reporting_repository: ReportingRepositoryPort) -> None:
        self._reporting_repository = reporting_repository

    async def execute(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> CfdiListResponse:
        return await self._reporting_repository.get_cfdi_list(user_id, page, page_size)
