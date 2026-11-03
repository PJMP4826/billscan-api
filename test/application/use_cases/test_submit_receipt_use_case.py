import asyncio
from typing import Any

import pytest

from src.application.use_cases.submit_receipt_use_case import SubmitReceiptUseCase
from src.domain.enums.invoice_use import InvoiceUse
from src.domain.enums.tax_regime import TaxRegime
from src.domain.value_objects.user_id import UserId
from src.shared.errors.base_exception import BadRequestError

_USER_ID = "ac9890c6-194b-4b7e-9aa0-2caae7db6c17"


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
    def __init__(self, regimens: list[dict[str, Any]] | None = None) -> None:
        self._regimens = regimens or []
        self.calls: list[str] = []

    async def get_regimens_by_user_id(self, user_id: str) -> list[dict[str, Any]]:
        self.calls.append(user_id)
        return self._regimens


def _build_use_case(
    regimens: list[dict[str, Any]] | None = None,
) -> tuple[SubmitReceiptUseCase, _FakeQueuePublisher, _FakeFiscalInfoRepository]:
    queue_publisher = _FakeQueuePublisher()
    fiscal_info_repository = _FakeFiscalInfoRepository(regimens=regimens)
    use_case = SubmitReceiptUseCase(
        file_storage=_FakeFileStorage(),  # type: ignore[arg-type]
        receipt_job_details_repository=_FakeReceiptJobDetailsRepository(),  # type: ignore[arg-type]
        receipt_image_repository=_FakeReceiptImageRepository(),  # type: ignore[arg-type]
        queue_publisher=queue_publisher,  # type: ignore[arg-type]
        fiscal_info_repository=fiscal_info_repository,  # type: ignore[arg-type]
    )
    return use_case, queue_publisher, fiscal_info_repository


def _images() -> dict[str, list[dict[str, bytes | str]]]:
    return {"1": [{"file": b"bytes", "mime": "image/jpeg"}]}


def test_payload_includes_client_fiscal_preferences_as_sat_codes():
    use_case, queue_publisher, _ = _build_use_case(
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
    # Sin régimen no se consulta la información fiscal del usuario.
    assert fiscal_info_repository.calls == []


def test_execute_rejects_regimen_not_registered_for_the_user():
    use_case, queue_publisher, _ = _build_use_case(
        regimens=[{"code": "612", "description": "PF", "fecha_alta": None}]
    )

    with pytest.raises(BadRequestError):
        asyncio.run(
            use_case.execute(
                user_id=UserId(_USER_ID),
                grouped_images=_images(),
                auto_billing=False,
                regimen=TaxRegime.R601,
            )
        )

    assert queue_publisher.enqueued == []


def test_execute_rejects_regimen_when_user_has_none_registered():
    use_case, queue_publisher, _ = _build_use_case(regimens=[])

    with pytest.raises(BadRequestError):
        asyncio.run(
            use_case.execute(
                user_id=UserId(_USER_ID),
                grouped_images=_images(),
                auto_billing=False,
                regimen=TaxRegime.R601,
            )
        )

    assert queue_publisher.enqueued == []
