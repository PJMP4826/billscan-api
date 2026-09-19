from src.domain.ports.repositories.reporting_repository_port import (
    ReportingRepositoryPort,
)
from src.application.dtos.receipt_count_summary_dto import ReceiptCountSummary


class GetReceiptCountSummaryUseCase:
    def __init__(self, reporting_repository: ReportingRepositoryPort) -> None:
        self._reporting_repository = reporting_repository

    async def execute(self) -> ReceiptCountSummary:
        return await self._reporting_repository.get_receipt_count_summary()
