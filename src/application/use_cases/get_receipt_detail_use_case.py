from typing import Literal
from src.domain.ports.repositories.reporting_repository_port import (
    ReportingRepositoryPort,
)


class GetReceiptBaseDetailUseCase:
    def __init__(self, reporting_repository: ReportingRepositoryPort) -> None:
        self._reporting_repository = reporting_repository

    async def execute(
        self, receipt_uuid: str, detail_level: Literal["base", "full"] = "base"
    ) -> dict[str, str | None]:
        if detail_level == "full":
            return await self._reporting_repository.get_receipt_full_detail(
                receipt_uuid=receipt_uuid,
            )

        return await self._reporting_repository.get_receipt_base_detail(
            receipt_uuid=receipt_uuid,
        )
