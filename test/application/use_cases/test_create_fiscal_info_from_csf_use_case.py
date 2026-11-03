import asyncio
from datetime import date
from typing import Any

import pytest

from src.application.dtos.billing_customer_regime_dto import BillingCustomerRegimeDto
from src.application.dtos.csf_fiscal_identity_dto import CsfFiscalIdentityDto
from src.application.use_cases.create_fiscal_info_from_csf_use_case import (
    CreateFiscalInfoFromCsfUseCase,
)
from src.domain.enums.tax_regime import TaxRegime
from src.domain.value_objects.user_id import UserId
from src.shared.errors.base_exception import BadRequestError

_USER_ID = "ac9890c6-194b-4b7e-9aa0-2caae7db6c17"
_PDF_BYTES = b"%PDF-1.4\n%fake\n"


class _FakeEncryptor:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def encrypt(self, value: str) -> str:
        self.calls.append(value)
        return f"enc({value})"


class _FakeFiscalInfoRepository:
    def __init__(self) -> None:
        self.inserted: list[dict[str, Any]] = []
        self.regimens: list[dict[str, Any]] = []

    async def insert_fiscal_info(self, **kwargs: Any) -> int:
        self.inserted.append(kwargs)
        return 42

    async def add_regimen(self, **kwargs: Any) -> int:
        self.regimens.append(kwargs)
        return len(self.regimens)


class _FakeExtractor:
    def __init__(self, dto: CsfFiscalIdentityDto | None = None) -> None:
        self._dto = dto
        self.calls: list[dict[str, Any]] = []

    async def extract(self, file_bytes: bytes, mime_type: str) -> CsfFiscalIdentityDto:
        self.calls.append({"file_bytes": file_bytes, "mime_type": mime_type})
        if self._dto is None:
            raise BadRequestError("La constancia no es legible")
        return self._dto


def _csf_dto(*regimens: TaxRegime) -> CsfFiscalIdentityDto:
    return CsfFiscalIdentityDto(
        razon_social="ACME SA DE CV",
        rfc="ACM010101AAA",
        cp="06600",
        regimens=[BillingCustomerRegimeDto(code=regimen) for regimen in regimens],
        address="CALLE REFORMA 222, JUAREZ, CUAUHTEMOC, CIUDAD DE MEXICO",
    )


def _build_use_case(dto: CsfFiscalIdentityDto | None = None) -> tuple[
    CreateFiscalInfoFromCsfUseCase,
    _FakeFiscalInfoRepository,
    _FakeEncryptor,
    _FakeExtractor,
]:
    repository = _FakeFiscalInfoRepository()
    encryptor = _FakeEncryptor()
    extractor = _FakeExtractor(dto)

    use_case = CreateFiscalInfoFromCsfUseCase(
        fiscal_info_repository=repository,  # type: ignore[arg-type]
        encryptor=encryptor,  # type: ignore[arg-type]
        extractor=extractor,  # type: ignore[arg-type]
    )
    return use_case, repository, encryptor, extractor


def test_execute_persists_all_regimens_from_csf():
    dto = _csf_dto(TaxRegime.R601, TaxRegime.R612)
    use_case, repository, _, extractor = _build_use_case(dto)

    asyncio.run(
        use_case.execute(
            user_id=UserId(_USER_ID),
            file_bytes=_PDF_BYTES,
            mime_type="application/pdf",
            email="facturas@acme.mx",
            use_cfdi_code_default="G03",
        )
    )

    # El archivo se delega al extractor tal cual lo recibió el caso de uso
    assert extractor.calls == [
        {"file_bytes": _PDF_BYTES, "mime_type": "application/pdf"}
    ]

    # Un solo registro de info fiscal, con los datos de la constancia
    assert len(repository.inserted) == 1
    inserted = repository.inserted[0]
    assert inserted["user_id"] == _USER_ID
    assert inserted["rfc"] == "enc(ACM010101AAA)"
    assert inserted["razon_social"] == "enc(ACME SA DE CV)"
    assert inserted["email"] == "enc(facturas@acme.mx)"
    assert inserted["cp"] == "enc(06600)"
    assert (
        inserted["address"]
        == "enc(CALLE REFORMA 222, JUAREZ, CUAUHTEMOC, CIUDAD DE MEXICO)"
    )
    assert inserted["use_cfdi_code_default"] == "G03"

    # La constancia trae dos regímenes vigentes: se guardan los dos
    assert len(repository.regimens) == 2
    assert [r["regimen_code"] for r in repository.regimens] == ["601", "612"]
    assert all(r["fiscal_info_id"] == 42 for r in repository.regimens)
    assert all(r["fecha_alta"] == date.today() for r in repository.regimens)
    assert repository.regimens[0]["regimen_description"] == TaxRegime.R601.description


def test_execute_does_not_encrypt_empty_address():
    dto = CsfFiscalIdentityDto(
        razon_social="ACME SA DE CV",
        rfc="ACM010101AAA",
        cp="06600",
        regimens=[BillingCustomerRegimeDto(code=TaxRegime.R601)],
        address=None,
    )
    use_case, repository, _, _ = _build_use_case(dto)

    asyncio.run(
        use_case.execute(
            user_id=UserId(_USER_ID),
            file_bytes=_PDF_BYTES,
            mime_type="application/pdf",
            email="facturas@acme.mx",
            use_cfdi_code_default="G03",
        )
    )

    assert repository.inserted[0]["address"] is None


def test_execute_propagates_bad_request_from_extractor():
    use_case, repository, _, _ = _build_use_case(None)

    with pytest.raises(BadRequestError):
        asyncio.run(
            use_case.execute(
                user_id=UserId(_USER_ID),
                file_bytes=b"no-es-un-pdf",
                mime_type="application/pdf",
                email="facturas@acme.mx",
                use_cfdi_code_default="G03",
            )
        )

    # Nada se persiste si el extractor falla
    assert repository.inserted == []
    assert repository.regimens == []
