import asyncio
from datetime import datetime
from typing import Any

import pytest

from src.application.use_cases.create_fiscal_info_use_case import (
    CreateFiscalInfoUseCase,
)
from src.domain.enums.tax_regime import TaxRegime

_USER_ID = "ac9890c6-194b-4b7e-9aa0-2caae7db6c17"
_FECHA_ALTA_SAT = datetime(2024, 1, 15, 10, 30)


class _FakeEncryptor:
    def encrypt(self, value: str) -> str:
        return f"enc({value})"


class _FakeFiscalInfoRepository:
    def __init__(self) -> None:
        self.inserted: list[dict[str, Any]] = []
        self.regimens: list[dict[str, Any]] = []

    async def insert_fiscal_info(self, **kwargs: Any) -> int:
        self.inserted.append(kwargs)
        return 7

    async def add_regimen(self, **kwargs: Any) -> int:
        self.regimens.append(kwargs)
        return len(self.regimens)


def _build_use_case() -> tuple[CreateFiscalInfoUseCase, _FakeFiscalInfoRepository]:
    repository = _FakeFiscalInfoRepository()
    use_case = CreateFiscalInfoUseCase(
        fiscal_info_repository=repository,  # type: ignore[arg-type]
        encryptor=_FakeEncryptor(),  # type: ignore[arg-type]
    )
    return use_case, repository


def test_execute_persists_encrypted_info_and_regimen():
    use_case, repository = _build_use_case()

    asyncio.run(
        use_case.execute(
            user_id=_USER_ID,
            rfc="ACM010101AAA",
            razon_social="ACME SA DE CV",
            email="facturas@acme.mx",
            cp="06600",
            address="CALLE REFORMA 222",
            regimen_code="601",
            fecha_alta_sat=_FECHA_ALTA_SAT,
            use_cfdi_code_default="G03",
        )
    )

    assert len(repository.inserted) == 1
    inserted = repository.inserted[0]
    assert inserted["rfc"] == "enc(ACM010101AAA)"
    assert inserted["razon_social"] == "enc(ACME SA DE CV)"
    assert inserted["email"] == "enc(facturas@acme.mx)"
    assert inserted["cp"] == "enc(06600)"
    assert inserted["address"] == "enc(CALLE REFORMA 222)"
    assert inserted["use_cfdi_code_default"] == "G03"

    assert repository.regimens == [
        {
            "fiscal_info_id": 7,
            "regimen_code": "601",
            "regimen_description": TaxRegime.R601.description,
            "fecha_alta": _FECHA_ALTA_SAT,
        }
    ]


def test_execute_raises_value_error_on_invalid_regimen():
    use_case, repository = _build_use_case()

    with pytest.raises(ValueError):
        asyncio.run(
            use_case.execute(
                user_id=_USER_ID,
                rfc="ACM010101AAA",
                razon_social="ACME SA DE CV",
                email="facturas@acme.mx",
                cp="06600",
                address=None,
                regimen_code="999",
                fecha_alta_sat=_FECHA_ALTA_SAT,
                use_cfdi_code_default="G03",
            )
        )

    # Se valida antes de tocar la base de datos
    assert repository.inserted == []
    assert repository.regimens == []
