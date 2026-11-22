import asyncio
from datetime import datetime
from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from src.application.dtos.billing_customer_regime_dto import BillingCustomerRegimeDto
from src.application.use_cases.create_fiscal_info_use_case import (
    CreateFiscalInfoUseCase,
)
from src.domain.enums.tax_regime import TaxRegime
from src.domain.value_objects.user_id import UserId

_USER_ID = "ac9890c6-194b-4b7e-9aa0-2caae7db6c17"
_FECHA_ALTA_SAT = datetime(2024, 1, 15, 10, 30)


class _FakeEncryptor:
    def encrypt(self, value: str) -> str:
        return f"enc({value})"


class _FakeFiscalInfoRepository:
    def __init__(self) -> None:
        self.inserted: list[dict[str, Any]] = []
        self.regimens_by_fiscal_info: dict[int, list[tuple[str, str, Any]]] = {}
        self.ids_by_user: dict[str, int] = {}

    async def upsert_fiscal_info(self, **kwargs: Any) -> tuple[int, bool]:
        self.inserted.append(kwargs)
        user_id = kwargs["user_id"]
        created = user_id not in self.ids_by_user
        if created:
            self.ids_by_user[user_id] = 7
        return self.ids_by_user[user_id], created

    async def replace_regimens(
        self, fiscal_info_id: int, regimens: list[tuple[str, str, Any]]
    ) -> None:
        self.regimens_by_fiscal_info[fiscal_info_id] = list(regimens)


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
            user_id=UserId(_USER_ID),
            rfc="ACM010101AAA",
            razon_social="ACME SA DE CV",
            email="facturas@acme.mx",
            cp="06600",
            address="CALLE REFORMA 222",
            regimens=[
                BillingCustomerRegimeDto(
                    code=TaxRegime.R601, fecha_alta_sat=_FECHA_ALTA_SAT
                )
            ],
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

    assert repository.regimens_by_fiscal_info[7] == [
        ("601", TaxRegime.R601.description, _FECHA_ALTA_SAT)
    ]


def test_execute_is_idempotent_and_replaces_regimens_for_same_user():
    use_case, repository = _build_use_case()

    first_created = asyncio.run(
        use_case.execute(
            user_id=UserId(_USER_ID),
            rfc="ACM010101AAA",
            razon_social="ACME SA DE CV",
            email="facturas@acme.mx",
            cp="06600",
            address="CALLE REFORMA 222",
            regimens=[
                BillingCustomerRegimeDto(
                    code=TaxRegime.R601, fecha_alta_sat=_FECHA_ALTA_SAT
                )
            ],
            use_cfdi_code_default="G03",
        )
    )
    second_created = asyncio.run(
        use_case.execute(
            user_id=UserId(_USER_ID),
            rfc="ACM010101AAA",
            razon_social="ACME SA DE CV",
            email="facturas@acme.mx",
            cp="06700",
            address="CALLE REFORMA 333",
            regimens=[
                BillingCustomerRegimeDto(
                    code=TaxRegime.R612, fecha_alta_sat=_FECHA_ALTA_SAT
                )
            ],
            use_cfdi_code_default="G03",
        )
    )

    assert first_created is True
    assert second_created is False
    assert len(repository.inserted) == 2
    assert repository.ids_by_user[_USER_ID] == 7
    assert repository.regimens_by_fiscal_info[7] == [
        ("612", TaxRegime.R612.description, _FECHA_ALTA_SAT)
    ]


def test_invalid_regimen_is_rejected_before_persisting():
    """El régimen llega tipado: un código fuera del enum no se puede construir.

    La validación ocurre en el borde (request/`BillingCustomerRegimeDto`), así
    que el caso de uso nunca ve un código inválido ni toca la base de datos.
    """
    adapter = TypeAdapter(BillingCustomerRegimeDto)

    with pytest.raises(ValidationError):
        adapter.validate_python({"code": "999"})

    with pytest.raises(ValueError):
        TaxRegime("999")
