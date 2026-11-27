import asyncio
from typing import Any

from src.application.dtos.cfdi.cfdi_dto import CfdiDto
from src.application.dtos.cfdi.complemento_dto import (
    ComplementoDto,
    TimbreFiscalDigitalDto,
)
from src.application.dtos.cfdi.emisor_dto import EmisorDto
from src.application.dtos.cfdi.receptor_dto import ReceptorDto
from src.application.dtos.invoice_result_dto import InvoiceResult
from src.application.use_cases.process_facturagpt_webhook_use_case import (
    ProcessFacturaGPTWebhookUseCase,
)
from src.domain.enums.billing_status import BillingStatus

_RECEIPT_ID = 42


def _cfdi() -> CfdiDto:
    return CfdiDto(
        emisor=EmisorDto(
            rfc="XAXX010101000",
            nombre="Comercializadora Ejemplo",
            regimen_fiscal="601",
        ),
        receptor=ReceptorDto(
            rfc="XAXX010101000",
            nombre="Cliente",
            domicilio_fiscal_receptor="01000",
            regimen_fiscal_receptor="601",
            uso_cfdi="G01",
        ),
        conceptos=[],
        complemento=ComplementoDto(
            timbre_fiscal_digital=TimbreFiscalDigitalDto(
                version="1.1",
                uuid="00000000-0000-0000-0000-000000000000",
                fecha_timbrado="2026-11-27T00:00:00",
                rfc_prov_certif="AAA010101AAA",
            )
        ),
        version="4.0",
        fecha="2026-11-27",
        forma_pago="01",
        sub_total=100.0,
        moneda="MXN",
        total=116.0,
        tipo_de_comprobante="I",
        exportacion="01",
        metodo_pago="PUE",
        lugar_expedicion="01000",
    )


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


class _FakePushTokenRepository:
    def __init__(self, tokens: list[str] | None = None) -> None:
        self._tokens = tokens or []
        self.requested_user_ids: list[str] = []

    async def find_tokens_by_user_id(self, user_id: str) -> list[str]:
        self.requested_user_ids.append(user_id)
        return self._tokens


class _FakePushNotificator:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    async def send(self, notification: Any, tokens: list[str]) -> list[Any]:
        self.sent.append({"notification": notification, "tokens": tokens})
        return []


class _FakeReceiptRepository:
    def __init__(self, user_id: str | None = "user-1") -> None:
        self._user_id = user_id

    async def find_user_id_by_receipt_id(self, receipt_id: int) -> str | None:
        return self._user_id


def _build_use_case(
    detail_repository: _FakeBillingDetailRepository,
    quota_repository: _FakeInvoiceQuotaRepository,
    receipt_repository: Any = None,
    push_token_repository: Any = None,
    push_notificator: Any = None,
) -> ProcessFacturaGPTWebhookUseCase:
    return ProcessFacturaGPTWebhookUseCase(
        webhook_repository=object(),  # type: ignore[arg-type]
        receipt_repository=receipt_repository or object(),
        billing_detail_repository=detail_repository,  # type: ignore[arg-type]
        billing_file_repository=object(),  # type: ignore[arg-type]
        webhook_handler=object(),  # type: ignore[arg-type]
        billing_provider=object(),  # type: ignore[arg-type]
        file_storage=object(),  # type: ignore[arg-type]
        invoice_quota_repository=quota_repository,  # type: ignore[arg-type]
        push_notificator=push_notificator or object(),
        push_token_repository=push_token_repository or object(),
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


def test_notify_sends_push_to_all_user_tokens():
    receipt_repository = _FakeReceiptRepository(user_id="user-1")
    token_repository = _FakePushTokenRepository(tokens=["tok-a", "tok-b"])
    push_notificator = _FakePushNotificator()
    use_case = _build_use_case(
        _FakeBillingDetailRepository(),
        _FakeInvoiceQuotaRepository(),
        receipt_repository=receipt_repository,
        push_token_repository=token_repository,
        push_notificator=push_notificator,
    )
    cfdi = _cfdi()

    asyncio.run(
        use_case._notify_invoice_ready(
            receipt_id=_RECEIPT_ID,
            receipt_uuid="uuid-1",
            cfdi=cfdi,
        )
    )

    assert token_repository.requested_user_ids == ["user-1"]
    assert len(push_notificator.sent) == 1
    assert push_notificator.sent[0]["tokens"] == ["tok-a", "tok-b"]
    assert (
        push_notificator.sent[0]["notification"].data["receipt_uuid"] == "uuid-1"
    )


def test_notify_skips_when_receipt_has_no_user():
    receipt_repository = _FakeReceiptRepository(user_id=None)
    token_repository = _FakePushTokenRepository(tokens=["tok-a"])
    push_notificator = _FakePushNotificator()
    use_case = _build_use_case(
        _FakeBillingDetailRepository(),
        _FakeInvoiceQuotaRepository(),
        receipt_repository=receipt_repository,
        push_token_repository=token_repository,
        push_notificator=push_notificator,
    )

    asyncio.run(
        use_case._notify_invoice_ready(
            receipt_id=_RECEIPT_ID,
            receipt_uuid="uuid-1",
            cfdi=_cfdi(),
        )
    )

    assert token_repository.requested_user_ids == []
    assert push_notificator.sent == []


def test_notify_is_best_effort_on_push_failure():
    receipt_repository = _FakeReceiptRepository(user_id="user-1")
    token_repository = _FakePushTokenRepository(tokens=["tok-a"])

    class _FailingPushNotificator:
        async def send(self, notification: Any, tokens: list[str]) -> list[Any]:
            raise RuntimeError("expo caído")

    use_case = _build_use_case(
        _FakeBillingDetailRepository(),
        _FakeInvoiceQuotaRepository(),
        receipt_repository=receipt_repository,
        push_token_repository=token_repository,
        push_notificator=_FailingPushNotificator(),
    )

    # No debe lanzar: el webhook ya quedó aplicado.
    asyncio.run(
        use_case._notify_invoice_ready(
            receipt_id=_RECEIPT_ID,
            receipt_uuid="uuid-1",
            cfdi=_cfdi(),
        )
    )
