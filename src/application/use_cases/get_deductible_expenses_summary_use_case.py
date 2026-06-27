from src.domain.ports.repositories.reporting_repository_port import (
    ReportingRepositoryPort,
)
from src.infrastructure.records.deductible_expense_summary import (
    DeductibleExpenseSummary,
)


class GetDeductibleExpensesSummaryUseCase:
    def __init__(self, reporting_repository: ReportingRepositoryPort) -> None:
        self._reporting_repository = reporting_repository

    async def execute(self) -> DeductibleExpenseSummary:
        return await self._reporting_repository.get_deductible_expenses_summary()
