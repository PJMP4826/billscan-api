import asyncio
from typing import Any

from src.application.dtos.invoice_result_dto import InvoiceResult
from src.application.use_cases.process_facturagpt_webhook_use_case import (
    ProcessFacturaGPTWebhookUseCase,
)
from src.domain.enums.billing_status import BillingStatus

_RECEIPT_ID = 42


class _FakeBillingDetailRepository:
    def __init__(self) -> None:
        self.status_updates: list[dict[str, Any]] = []

    async def update_billing_status(self, **kwargs: Any) -> None:
        self.status_updates.append(kwargs)


class _FakeInvoiceQuotaRepository:
    def __init__(self) -> None:
        self.consumed: list[int] = []
        self.released: list[int] = []

    async def mark_consumed(self, receipt_id: int) -> None:
        self.consumed.append(receipt_id)

    async def release(self, receipt_id: int) -> None:
        self.released.append(receipt_id)

    async def try_reserve(
        self, receipt_id: int, rfc_hash: str, max_invoices: int
    ) -> bool:
        return True

    async def count_in_use(self, rfc_hash: str) -> int:
        return 0


def _build_use_case(
    detail_repository: _FakeBillingDetailRepository,
    quota_repository: _FakeInvoiceQuotaRepository,
) -> ProcessFacturaGPTWebhookUseCase:
    return ProcessFacturaGPTWebhookUseCase(
        webhook_repository=object(),  # type: ignore[arg-type]
        receipt_repository=object(),  # type: ignore[arg-type]
        billing_detail_repository=detail_repository,  # type: ignore[arg-type]
        billing_file_repository=object(),  # type: ignore[arg-type]
        webhook_handler=object(),  # type: ignore[arg-type]
        billing_provider=object(),  # type: ignore[arg-type]
        file_storage=object(),  # type: ignore[arg-type]
        invoice_quota_repository=quota_repository,  # type: ignore[arg-type]
    )


def test_completed_event_marks_quota_as_consumed():
    detail_repository = _FakeBillingDetailRepository()
    quota_repository = _FakeInvoiceQuotaRepository()
    use_case = _build_use_case(detail_repository, quota_repository)

    asyncio.run(
        use_case._apply_completed(
            receipt_id=_RECEIPT_ID,
            idempotency_key="evt-1",
            invoice_result=InvoiceResult(session_id="session-1"),
        )
    )

    assert quota_repository.consumed == [_RECEIPT_ID]
    assert quota_repository.released == []
    assert detail_repository.status_updates[0]["billing_status"] == (
        BillingStatus.COMPLETED.value
    )


def test_failed_event_releases_quota():
    detail_repository = _FakeBillingDetailRepository()
    quota_repository = _FakeInvoiceQuotaRepository()
    use_case = _build_use_case(detail_repository, quota_repository)

    asyncio.run(
        use_case._apply_failed(
            receipt_id=_RECEIPT_ID,
            invoice_result=InvoiceResult(
                session_id="session-2",
                error_code="INVALID_RFC",
                error_message="RFC inválido",
            ),
        )
    )

    assert quota_repository.released == [_RECEIPT_ID]
    assert quota_repository.consumed == []
    assert detail_repository.status_updates[0]["billing_status"] == (
        BillingStatus.FAILED.value
    )
