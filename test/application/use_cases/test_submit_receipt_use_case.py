import asyncio
from typing import Any

import pytest

from src.application.use_cases.submit_receipt_use_case import SubmitReceiptUseCase
from src.domain.enums.invoice_use import InvoiceUse
from src.domain.enums.tax_regime import TaxRegime
from src.domain.errors.fiscal_info_error import (
    FiscalInfoNotFoundError,
    FiscalInfoRequiredError,
    InvalidFiscalDataError,
)
from src.domain.errors.invoice_use_tax_regime_error import (
    InvalidInvoiceUseTaxRegimeCombinationError,
    InvoiceUseNotAllowedForPersonTypeError,
    NoRegisteredRegimenAllowsInvoiceUseError,
    TaxRegimeNotAllowedForPersonTypeError,
    UnknownInvoiceUseError,
)
from src.domain.errors.regimen_error import (
    NoRegisteredRegimensError,
    RegimenNotRegisteredError,
)
from src.domain.value_objects.user_id import UserId
from src.shared.errors.base_exception import BadRequestError

_USER_ID = "ac9890c6-194b-4b7e-9aa0-2caae7db6c17"
_RFC_FISICA = "AACM010101AAA"
_RFC_MORAL = "ACM010101AAA"


class _FakeEncryptor:
    def decrypt(self, value: str) -> str:
        if value.startswith("enc(") and value.endswith(")"):
            return value[4:-1]
        return value


class _FakeFileStorage:
    async def upload(self, key: str, data: bytes, mime_type: str) -> str:
        return f"key/{key}"


class _FakeReceiptJobDetailsRepository:
    def __init__(self) -> None:
        self.created = 0

    async def create(self, user_id: str, job_name: str) -> int:
        self.created += 1
        return 100 + self.created


class _FakeReceiptImageRepository:
    def __init__(self) -> None:
        self.inserted: list[dict[str, Any]] = []

    async def insert(self, **kwargs: Any) -> int:
        self.inserted.append(kwargs)
        return len(self.inserted)


class _FakeQueuePublisher:
    def __init__(self) -> None:
        self.enqueued: list[dict[str, Any]] = []

    def enqueue_job(self, job_name: str, payload: dict[str, Any]) -> None:
        self.enqueued.append({"job_name": job_name, "payload": payload})


class _FakeFiscalInfoRepository:
    def __init__(
        self,
        regimens: list[dict[str, Any]] | None = None,
        rfc: str | None = _RFC_FISICA,
    ) -> None:
        self._regimens = regimens or []
        self._rfc = rfc
        self.regimen_calls: list[str] = []
        self.rfc_calls: list[str] = []

    async def get_regimens_by_user_id(self, user_id: str) -> list[dict[str, Any]]:
        self.regimen_calls.append(user_id)
        return self._regimens

    async def get_rfc_by_user_id(self, user_id: str) -> str:
        self.rfc_calls.append(user_id)
        if self._rfc is None:
            raise FiscalInfoNotFoundError()
        return f"enc({self._rfc})"


def _build_use_case(
    regimens: list[dict[str, Any]] | None = None,
    rfc: str | None = _RFC_FISICA,
) -> tuple[SubmitReceiptUseCase, _FakeQueuePublisher, _FakeFiscalInfoRepository]:
    queue_publisher = _FakeQueuePublisher()
    fiscal_info_repository = _FakeFiscalInfoRepository(regimens=regimens, rfc=rfc)
    use_case = SubmitReceiptUseCase(
        file_storage=_FakeFileStorage(),  # type: ignore[arg-type]
        receipt_job_details_repository=_FakeReceiptJobDetailsRepository(),  # type: ignore[arg-type]
        receipt_image_repository=_FakeReceiptImageRepository(),  # type: ignore[arg-type]
        queue_publisher=queue_publisher,  # type: ignore[arg-type]
        fiscal_info_repository=fiscal_info_repository,  # type: ignore[arg-type]
        data_encryptor=_FakeEncryptor(),  # type: ignore[arg-type]
    )
    return use_case, queue_publisher, fiscal_info_repository


def _images() -> dict[str, list[dict[str, bytes | str]]]:
    return {"1": [{"file": b"bytes", "mime": "image/jpeg"}]}


def test_payload_includes_client_fiscal_preferences_as_sat_codes():
    use_case, queue_publisher, fiscal_info_repository = _build_use_case(
        regimens=[{"code": "612", "description": "PF", "fecha_alta": None}]
    )

    asyncio.run(
        use_case.execute(
            user_id=UserId(_USER_ID),
            grouped_images=_images(),
            auto_billing=True,
            uso_cfdi=InvoiceUse.D01,
            regimen=TaxRegime.R612,
        )
    )

    payload = queue_publisher.enqueued[0]["payload"]
    assert payload["uso_cfdi"] == "D01"
    assert payload["regimen"] == "612"
    assert payload["auto_billing"] is True
    assert fiscal_info_repository.rfc_calls == [_USER_ID]
    assert fiscal_info_repository.regimen_calls == [_USER_ID]


def test_payload_defaults_preferences_to_none():
    use_case, queue_publisher, fiscal_info_repository = _build_use_case()

    asyncio.run(
        use_case.execute(
            user_id=UserId(_USER_ID),
            grouped_images=_images(),
            auto_billing=False,
        )
    )

    payload = queue_publisher.enqueued[0]["payload"]
    assert payload["uso_cfdi"] is None
    assert payload["regimen"] is None
    assert fiscal_info_repository.rfc_calls == []
    assert fiscal_info_repository.regimen_calls == []


def test_payload_with_uso_without_regimen_uses_compatible_regimen():
    use_case, queue_publisher, fiscal_info_repository = _build_use_case(
        regimens=[{"code": "612", "description": "PF", "fecha_alta": None}]
    )

    asyncio.run(
        use_case.execute(
            user_id=UserId(_USER_ID),
            grouped_images=_images(),
            auto_billing=True,
            uso_cfdi=InvoiceUse.G01,
        )
    )

    payload = queue_publisher.enqueued[0]["payload"]
    assert payload["uso_cfdi"] == "G01"
    assert payload["regimen"] is None
    assert fiscal_info_repository.rfc_calls == [_USER_ID]
    assert fiscal_info_repository.regimen_calls == [_USER_ID]


def test_execute_rejects_regimen_not_registered_for_the_user():
    use_case, queue_publisher, _ = _build_use_case(
        regimens=[{"code": "612", "description": "PF", "fecha_alta": None}]
    )

    with pytest.raises(RegimenNotRegisteredError) as exc_info:
        asyncio.run(
            use_case.execute(
                user_id=UserId(_USER_ID),
                grouped_images=_images(),
                auto_billing=False,
                regimen=TaxRegime.R601,
            )
        )

    assert exc_info.value.error_code == "REGIMEN_NOT_REGISTERED"
    assert exc_info.value.details["regimen"] == "601"
    assert queue_publisher.enqueued == []


def test_execute_rejects_regimen_when_user_has_none_registered():
    use_case, queue_publisher, _ = _build_use_case(regimens=[])

    with pytest.raises(NoRegisteredRegimensError):
        asyncio.run(
            use_case.execute(
                user_id=UserId(_USER_ID),
                grouped_images=_images(),
                auto_billing=False,
                regimen=TaxRegime.R601,
            )
        )

    assert queue_publisher.enqueued == []


def test_execute_rejects_invalid_uso_for_user_person_type():
    use_case, queue_publisher, _ = _build_use_case(
        regimens=[{"code": "612", "description": "PF", "fecha_alta": None}],
        rfc=_RFC_MORAL,
    )

    with pytest.raises(InvoiceUseNotAllowedForPersonTypeError) as exc_info:
        asyncio.run(
            use_case.execute(
                user_id=UserId(_USER_ID),
                grouped_images=_images(),
                auto_billing=False,
                uso_cfdi=InvoiceUse.D01,
            )
        )

    assert isinstance(exc_info.value, BadRequestError)
    assert queue_publisher.enqueued == []


def test_execute_rejects_uso_without_compatible_registered_regimen():
    use_case, queue_publisher, _ = _build_use_case(
        regimens=[{"code": "605", "description": "PF", "fecha_alta": None}]
    )

    with pytest.raises(NoRegisteredRegimenAllowsInvoiceUseError) as exc_info:
        asyncio.run(
            use_case.execute(
                user_id=UserId(_USER_ID),
                grouped_images=_images(),
                auto_billing=False,
                uso_cfdi=InvoiceUse.G01,
            )
        )

    assert isinstance(exc_info.value, BadRequestError)
    assert exc_info.value.details["registered_regimes"] == ["605"]
    assert queue_publisher.enqueued == []


def test_execute_rejects_uso_when_user_has_no_registered_regimens():
    use_case, queue_publisher, _ = _build_use_case(regimens=[])

    with pytest.raises(NoRegisteredRegimensError):
        asyncio.run(
            use_case.execute(
                user_id=UserId(_USER_ID),
                grouped_images=_images(),
                auto_billing=False,
                uso_cfdi=InvoiceUse.G01,
            )
        )

    assert queue_publisher.enqueued == []


def test_execute_rejects_invalid_uso_and_regimen_combination():
    use_case, queue_publisher, _ = _build_use_case(
        regimens=[{"code": "601", "description": "PM", "fecha_alta": None}]
    )

    with pytest.raises(InvalidInvoiceUseTaxRegimeCombinationError):
        asyncio.run(
            use_case.execute(
                user_id=UserId(_USER_ID),
                grouped_images=_images(),
                auto_billing=False,
                uso_cfdi=InvoiceUse.D01,
                regimen=TaxRegime.R601,
            )
        )

    assert queue_publisher.enqueued == []


def test_execute_rejects_regimen_not_allowed_for_person_type():
    use_case, queue_publisher, _ = _build_use_case(
        regimens=[{"code": "601", "description": "PM", "fecha_alta": None}]
    )

    with pytest.raises(TaxRegimeNotAllowedForPersonTypeError):
        asyncio.run(
            use_case.execute(
                user_id=UserId(_USER_ID),
                grouped_images=_images(),
                auto_billing=False,
                uso_cfdi=InvoiceUse.G01,
                regimen=TaxRegime.R601,
            )
        )

    assert queue_publisher.enqueued == []


def test_execute_rejects_unsupported_uso():
    use_case, queue_publisher, _ = _build_use_case(
        regimens=[{"code": "612", "description": "PF", "fecha_alta": None}]
    )

    with pytest.raises(UnknownInvoiceUseError):
        asyncio.run(
            use_case.execute(
                user_id=UserId(_USER_ID),
                grouped_images=_images(),
                auto_billing=False,
                uso_cfdi=InvoiceUse.P01,
            )
        )

    assert queue_publisher.enqueued == []


def test_execute_rejects_invalid_rfc():
    use_case, queue_publisher, _ = _build_use_case(
        regimens=[{"code": "612", "description": "PF", "fecha_alta": None}],
        rfc="TOO-SHORT",
    )

    with pytest.raises(InvalidFiscalDataError) as exc_info:
        asyncio.run(
            use_case.execute(
                user_id=UserId(_USER_ID),
                grouped_images=_images(),
                auto_billing=False,
                uso_cfdi=InvoiceUse.G01,
            )
        )

    assert exc_info.value.error_code == "INVALID_FISCAL_DATA"
    assert "TOO-SHORT" not in str(exc_info.value)
    assert queue_publisher.enqueued == []


def test_execute_rejects_uso_when_user_has_no_fiscal_info():
    use_case, queue_publisher, _ = _build_use_case(rfc=None)

    with pytest.raises(FiscalInfoRequiredError) as exc_info:
        asyncio.run(
            use_case.execute(
                user_id=UserId(_USER_ID),
                grouped_images=_images(),
                auto_billing=False,
                uso_cfdi=InvoiceUse.G01,
            )
        )

    assert exc_info.value.error_code == "FISCAL_INFO_REQUIRED"
    assert queue_publisher.enqueued == []
