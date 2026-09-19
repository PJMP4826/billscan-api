from src.domain.ports.repositories.reporting_repository_port import (
    ReportingRepositoryPort,
)
from src.application.dtos.receipt_list_response_dto import ReceiptListResponse


class GetReceiptListUseCase:
    def __init__(self, reporting_repository: ReportingRepositoryPort) -> None:
        self._reporting_repository = reporting_repository

    async def execute(self, page: int = 1, page_size: int = 20) -> ReceiptListResponse:
        return await self._reporting_repository.get_receipt_list(page, page_size)
