from src.domain.ports.repositories.reporting_repository_port import (
    ReportingRepositoryPort,
)
from src.application.dtos.completed_billing_summary_dto import (
    CompletedBillingSummary,
)
from src.domain.value_objects.user_id import UserId


class GetCompletedBillingSummaryUseCase:
    def __init__(self, reporting_repository: ReportingRepositoryPort) -> None:
        self._reporting_repository = reporting_repository

    async def execute(
        self, user_id: UserId, period: str = "month"
    ) -> CompletedBillingSummary:
        return await self._reporting_repository.get_completed_billing_summary(
            user_id.value, period
        )
