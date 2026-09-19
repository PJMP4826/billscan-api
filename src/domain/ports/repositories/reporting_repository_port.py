from abc import ABC, abstractmethod
from typing import Any

from src.application.dtos.completed_billing_summary_dto import (
    CompletedBillingSummary,
)
from src.application.dtos.issued_cfdi_summary_dto import IssuedCFDISummary

class ReportingRepositoryPort(ABC):

    @abstractmethod
    async def get_completed_billing_summary(
        self, period: str = "month"
    ) -> CompletedBillingSummary:
        """
        Returns the total amount and count of receipts that have
        a COMPLETED billing status within the given period.
        Valid periods: month, year, 3years, 5years.
        """
        pass

    @abstractmethod
    async def get_issued_cfdi_summary(self) -> IssuedCFDISummary:
        """
        Returns the total amount and count of receipts that have
        an associated billing file and a COMPLETED billing status.
        """
        pass

    @abstractmethod
    async def get_recent_activity(
        self,
        receipt_uuid: str | None = None,
        status_filter: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Returns recent activity items ordered by creation date DESC.
        Optionally filtered by receipt_uuid or status.
        """
        pass

    @abstractmethod
    async def get_receipt_base_detail(self, receipt_uuid: str) -> dict[str, str | None]:
        """
        Returns the base fiscal detail of a single receipt,
        including merchant info, fiscal info, and payment method.
        """
        pass

    @abstractmethod
    async def get_receipt_full_detail(self, receipt_uuid: str) -> dict[str, str | None]:
        """
        Returns the full detail of a receipt including aggregated
        items, taxes, and payments as JSON arrays.
        """
        pass
