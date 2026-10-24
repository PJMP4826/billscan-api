import asyncio
from datetime import date, time
from decimal import Decimal
from typing import Any

import pytest

from src.application.use_cases.initiate_billing_use_case import (
    InitiateBillingUseCase,
)
from src.application.dtos.invoice_result_dto import InvoiceResult
from src.domain.entities.receipt import Receipt
from src.domain.enums.billing_status import BillingStatus
from src.domain.enums.invoice_use import InvoiceUse
from src.domain.enums.sat_payment_methods import (
    SatPaymentMethodCode,
    SatPaymentMethodDescription,
)
from src.domain.value_objects.line_item import LineItem
from src.domain.value_objects.merchant_data import MerchantData
from src.domain.value_objects.payment_info import PaymentInfo
from src.domain.value_objects.totals_and_taxes import TotalsAndTaxes
from src.domain.value_objects.transaction_metadata import TransactionMetadata

_RECEIPT_ID = 15
_USER_ID = "ac9890c6-194b-4b7e-9aa0-2caae7db6c17"


class _FakeEncryptor:
    def decrypt(self, value: str) -> str:
        return value.replace("enc(", "").rstrip(")") if value else value


class _FakeFileStorage:
    async def download(self, key: str) -> tuple[bytes, str]:
        return b"image-bytes", "image/jpeg"


class _FakeReceiptImageRepository:
    async def find_by_receipt_id(self, receipt_id: int) -> list[dict[str, Any]]:
        return [{"file_key": "folios/abc.jpg"}]


class _FakeFiscalInfoRepository:
    def __init__(self) -> None:
        self.default_uso_cfdi = "G03"
        self.default_regimen = "601"

    async def get_latest_by_user_id(self, user_id: str) -> dict[str, Any]:
        return {
            "fiscal_info_id": 1,
            "user_id": user_id,
            "rfc": "enc(ACM010101AAA)",
            "razon_social": "enc(ACME SA DE CV)",
            "fiscal_email": "enc(facturas@acme.mx)",
            "cp": "enc(06600)",
            "address": "enc(CALLE REFORMA 222)",
            "use_cfdi_default": self.default_uso_cfdi,
            "regimen_id": 9,
            "regimen_code": self.default_regimen,
            "regimen_description": "General de Ley Personas Morales",
            "fecha_alta": date(2026, 1, 1),
        }


class _FakeBillingDetailRepository:
    def __init__(self, detail: dict[str, Any] | None = None) -> None:
        self._detail = detail or {"receipt_id": _RECEIPT_ID}
        self.status_updates: list[dict[str, Any]] = []
        self.preference_updates: list[dict[str, Any]] = []

    async def find_by_receipt_id(self, receipt_id: int) -> dict[str, Any] | None:
        return self._detail

    async def set_billing_preferences(
        self,
        receipt_id: int,
        uso_cfdi: str | None = None,
        regimen_code: str | None = None,
    ) -> None:
        self.preference_updates.append(
            {
                "receipt_id": receipt_id,
                "uso_cfdi": uso_cfdi,
                "regimen_code": regimen_code,
            }
        )

    async def update_billing_status(self, **kwargs: Any) -> None:
        self.status_updates.append(kwargs)


class _FakeReceiptRepository:
    async def find_by_id(self, receipt_id: int) -> Receipt:
        return Receipt(
            receipt_uuid="37348a21bab649429916946b26a4d789",
            merchant=MerchantData(name="Comercio Ficticio", tax_id="CFI010101AA1"),
            transaction=TransactionMetadata(
                transaction_date=date(2026, 9, 24),
                transaction_time=time(12, 30, 0),
                ticket_number="T-1",
            ),
            items=[
                LineItem(
                    quantity=1.0,
                    description="Producto ficticio",
                    unit_price=Decimal("50.00"),
                    total_price=Decimal("50.00"),
                )
            ],
            totals=TotalsAndTaxes(
                subtotal=Decimal("50.00"),
                total_discount=Decimal("0.00"),
                taxes=[],
                total=Decimal("50.00"),
                amount_paid=Decimal("50.00"),
                change=Decimal("0.00"),
            ),
            payment=PaymentInfo(
                method_code=SatPaymentMethodCode.EFECTIVO,
                method_description=SatPaymentMethodDescription.EFECTIVO,
            ),
        )


class _FakeBillingProvider:
    def __init__(self, error: Exception | None = None) -> None:
        self.submitted: list[Any] = []
        self._error = error

    async def submit_invoice(self, request: Any) -> InvoiceResult:
        self.submitted.append(request)
        if self._error:
            raise self._error
        return InvoiceResult(session_id="session-123")


def _build_use_case(
    billing_detail_repository: _FakeBillingDetailRepository,
    billing_provider: _FakeBillingProvider | None = None,
) -> tuple[InitiateBillingUseCase, _FakeBillingProvider]:
    provider = billing_provider or _FakeBillingProvider()
    use_case = InitiateBillingUseCase(
        billing_provider=provider,  # type: ignore[arg-type]
        billing_detail_repository=billing_detail_repository,  # type: ignore[arg-type]
        fiscal_info_repository_port=_FakeFiscalInfoRepository(),  # type: ignore[arg-type]
        receipt_image_repository_port=_FakeReceiptImageRepository(),  # type: ignore[arg-type]
        receipt_repository=_FakeReceiptRepository(),  # type: ignore[arg-type]
        encryptor=_FakeEncryptor(),  # type: ignore[arg-type]
        file_storage=_FakeFileStorage(),  # type: ignore[arg-type]
    )
    return use_case, provider


def test_uses_persisted_preferences_sent_by_the_client():
    detail_repository = _FakeBillingDetailRepository(
        detail={
            "receipt_id": _RECEIPT_ID,
            "uso_cfdi": "D01",
            "regimen_code": "612",
        }
    )
    use_case, provider = _build_use_case(detail_repository)

    asyncio.run(
        use_case.execute(payload={"receipt_id": _RECEIPT_ID, "user_id": _USER_ID})
    )

    request = provider.submitted[0]
    assert request.invoice_use is InvoiceUse.D01
    assert request.customer_info.regimen.value == "612"
    assert detail_repository.status_updates[0]["billing_status"] == (
        BillingStatus.PROCESSING
    )


def test_falls_back_to_fiscal_info_defaults_when_nothing_persisted():
    detail_repository = _FakeBillingDetailRepository()
    use_case, provider = _build_use_case(detail_repository)

    asyncio.run(
        use_case.execute(payload={"receipt_id": _RECEIPT_ID, "user_id": _USER_ID})
    )

    request = provider.submitted[0]
    assert request.invoice_use is InvoiceUse.G03
    assert request.customer_info.regimen.value == "601"
    # Los valores efectivos se guardan para auditoría
    assert detail_repository.preference_updates == [
        {"receipt_id": _RECEIPT_ID, "uso_cfdi": "G03", "regimen_code": "601"}
    ]


def test_marks_billing_as_failed_when_provider_raises():
    detail_repository = _FakeBillingDetailRepository(
        detail={"receipt_id": _RECEIPT_ID, "uso_cfdi": "D01", "regimen_code": "612"}
    )
    provider = _FakeBillingProvider(error=RuntimeError("boom"))
    use_case, _ = _build_use_case(detail_repository, provider)

    asyncio.run(
        use_case.execute(payload={"receipt_id": _RECEIPT_ID, "user_id": _USER_ID})
    )

    assert detail_repository.status_updates[0]["billing_status"] == (
        BillingStatus.FAILED
    )
    assert detail_repository.status_updates[0]["billing_error_message"] == "boom"
