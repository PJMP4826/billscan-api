from abc import ABC, abstractmethod
from typing import Any

from src.application.dtos.cfdi_response_dto import CfdiResponseDto
from src.application.dtos.completed_billing_summary_dto import (
    CompletedBillingSummary,
)
from src.application.dtos.cfdi import CfdiListResponse
from src.application.dtos.receipt_count_summary_dto import ReceiptCountSummary
from src.application.dtos.receipt_list_response_dto import ReceiptListResponse

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
    async def get_receipt_count_summary(self) -> ReceiptCountSummary:
        """
        Returns the total count of receipts, split by billable and non-billable.
        """
        pass

    @abstractmethod
    async def get_receipt_list(self, page: int = 1, page_size: int = 20) -> ReceiptListResponse:
        """
        Returns a paginated list of receipts with merchant name,
        registration date, total, and billing status.
        """
        pass

    @abstractmethod
    async def get_receipt_full_detail(self, receipt_uuid: str) -> dict[str, str | None]:
        """
        Returns the full detail of a receipt including aggregated
        items, taxes, and payments as JSON arrays.
        """
        pass

    @abstractmethod
    async def get_cfdi_list(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> CfdiListResponse:
        """
        Returns a paginated projection of the CFDIs issued for the given
        user (emisor name, total, serie, folio, uso CFDI) extracted from
        the `cfdi_summary` JSONB column without hydrating the full CfdiDto.
        """
        pass

    @abstractmethod
    async def get_cfdi_detail(
        self, user_id: str, receipt_uuid: str
    ) -> CfdiResponseDto:
        """
        Returns the stored content of a single CFDI (`cfdi_summary` JSONB)
        plus the storage keys of its XML and PDF files. Raises ValueError
        when the receipt has no CFDI content.
        """
        pass
