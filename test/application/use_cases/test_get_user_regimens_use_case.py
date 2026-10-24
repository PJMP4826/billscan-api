import asyncio
from typing import Any

import pytest

from src.application.use_cases.get_user_regimens_use_case import (
    GetUserRegimensUseCase,
)
from src.shared.errors.base_exception import NotFoundError

_USER_ID = "ac9890c6-194b-4b7e-9aa0-2caae7db6c17"


class _FakeFiscalInfoRepository:
    def __init__(
        self,
        regimens: list[dict[str, Any]] | None = None,
        has_fiscal_info: bool = True,
    ) -> None:
        self._regimens = regimens or []
        self._has_fiscal_info = has_fiscal_info
        self.calls: list[str] = []

    async def get_regimens_by_user_id(self, user_id: str) -> list[dict[str, Any]]:
        self.calls.append(user_id)
        return self._regimens

    async def has_fiscal_info(self, user_id: str) -> bool:
        return self._has_fiscal_info


def _build_use_case(
    repository: _FakeFiscalInfoRepository,
) -> GetUserRegimensUseCase:
    return GetUserRegimensUseCase(
        fiscal_info_repository=repository,  # type: ignore[arg-type]
    )


def test_execute_returns_serialized_regimens():
    repository = _FakeFiscalInfoRepository(
        regimens=[
            {"code": "612", "description": "Personas Físicas", "fecha_alta": None},
            {"code": "601", "description": "General de Ley", "fecha_alta": None},
        ]
    )
    use_case = _build_use_case(repository)

    result = asyncio.run(use_case.execute(user_id=_USER_ID))

    assert result == [
        {"code": "612", "description": "Personas Físicas", "fecha_alta": None},
        {"code": "601", "description": "General de Ley", "fecha_alta": None},
    ]


def test_execute_raises_not_found_when_user_has_no_fiscal_info():
    repository = _FakeFiscalInfoRepository(regimens=[], has_fiscal_info=False)
    use_case = _build_use_case(repository)

    with pytest.raises(NotFoundError):
        asyncio.run(use_case.execute(user_id=_USER_ID))


def test_execute_returns_empty_list_when_fiscal_info_has_no_regimens():
    repository = _FakeFiscalInfoRepository(regimens=[], has_fiscal_info=True)
    use_case = _build_use_case(repository)

    assert asyncio.run(use_case.execute(user_id=_USER_ID)) == []
