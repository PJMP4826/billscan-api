from src.domain.ports.repositories.reporting_repository_port import (
    ReportingRepositoryPort,
)
from src.application.dtos.issued_cfdi_summary_dto import IssuedCFDISummary


class GetIssuedCFDISummaryUseCase:
    def __init__(self, reporting_repository: ReportingRepositoryPort) -> None:
        self._reporting_repository = reporting_repository

    async def execute(self) -> IssuedCFDISummary:
        return await self._reporting_repository.get_issued_cfdi_summary()
