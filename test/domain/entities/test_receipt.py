import json
from datetime import date, time
from decimal import Decimal

from src.application.dtos.receipt_detail_dto import ReceiptDetailDto
from src.domain.entities.receipt import Receipt
from src.domain.enums.sat_payment_methods import (
    SatPaymentMethodCode,
    SatPaymentMethodDescription,
)
from src.domain.value_objects.billing_data import BillingData
from src.domain.value_objects.line_item import LineItem
from src.domain.value_objects.merchant_data import MerchantData
from src.domain.value_objects.payment_info import PaymentInfo
from src.domain.value_objects.tax_detail import TaxDetail
from src.domain.value_objects.totals_and_taxes import TotalsAndTaxes
from src.domain.value_objects.transaction_metadata import TransactionMetadata

_FILE_URL = "https://storage.example.com/folios/abc.xml?X-Amz-Signature=abc"


def _build_receipt(**overrides) -> Receipt:
    defaults = dict(
        receipt_uuid="37348a21bab649429916946b26a4d789",
        merchant=MerchantData(name="Comercio Ficticio", tax_id="CFI010101AA1"),
        transaction=TransactionMetadata(
            transaction_date=date(2026, 9, 24),
            transaction_time=time(12, 30, 0),
            ticket_number="T-1",
        ),
        items=[
            LineItem(
                quantity=2.0,
                description="Producto ficticio",
                unit_price=Decimal("25.00"),
                total_price=Decimal("50.00"),
            )
        ],
        totals=TotalsAndTaxes(
            subtotal=Decimal("50.00"),
            total_discount=Decimal("0.00"),
            taxes=[
                TaxDetail(name="IVA 16%", rate=Decimal("0.16"), amount=Decimal("8.00"))
            ],
            total=Decimal("58.00"),
            amount_paid=Decimal("60.00"),
            change=Decimal("2.00"),
        ),
        payment=PaymentInfo(
            method_code=SatPaymentMethodCode.EFECTIVO,
            method_description=SatPaymentMethodDescription.EFECTIVO,
        ),
        billing=BillingData(is_billable=True, billing_url="https://example.com/b"),
    )
    defaults.update(overrides)
    return Receipt(**defaults)


def _build_detail(**overrides) -> ReceiptDetailDto:
    """El DTO de detalle aplica `json_safe` sobre la entidad de dominio."""
    return ReceiptDetailDto(
        receipt=_build_receipt(**overrides),
        file_url=_FILE_URL,
    )


def test_to_dict_is_json_serializable() -> None:
    data = _build_detail().to_dict()

    parsed = json.loads(json.dumps(data, ensure_ascii=False))

    assert parsed["receipt_uuid"] == "37348a21bab649429916946b26a4d789"
    assert parsed["file_url"] == _FILE_URL


def test_to_dict_converts_decimals_to_str() -> None:
    data = _build_detail().to_dict()

    assert data["totals"]["total"] == "58.00"
    assert data["totals"]["taxes"][0]["amount"] == "8.00"
    assert data["items"][0]["total_price"] == "50.00"
    assert isinstance(data["totals"]["total"], str)


def test_to_dict_converts_dates_and_times_to_isoformat() -> None:
    data = _build_detail().to_dict()

    assert data["transaction"]["transaction_date"] == "2026-09-24"
    assert data["transaction"]["transaction_time"] == "12:30:00"
    assert data["billing"]["expiration_date"] is None


def test_to_dict_converts_enums_to_values() -> None:
    data = _build_detail().to_dict()

    assert data["payment"]["method_code"] == "01"
    assert data["payment"]["method_description"] == "Efectivo"


def test_entity_to_dict_keeps_domain_types() -> None:
    """La entidad expone tipos de dominio; la conversión JSON es del DTO."""
    data = _build_receipt().to_dict()

    assert isinstance(data["totals"]["total"], Decimal)
    assert isinstance(data["transaction"]["transaction_date"], date)
    assert isinstance(data["payment"]["method_code"], SatPaymentMethodCode)


def test_to_dict_does_not_leak_storage_file_key() -> None:
    data = _build_detail().to_dict()

    assert "file_key" not in data
    assert data["file_url"] == _FILE_URL
