from typing import Any

from src.domain.ports.repositories.fiscal_info_repository_port import (
    FiscalInfoRepositoryPort,
)
from src.shared.errors.base_exception import NotFoundError


class GetUserRegimensUseCase:
    """Expone los regímenes fiscales del usuario para el selector del cliente.

    El cliente necesita conocer los regímenes asociados a su RFC **antes** de
    enviar el ticket, porque el régimen con el que se factura ya no se toma por
    defecto de la base de datos sino que lo elige en la request. La validación
    de esa elección vive en `SubmitReceiptUseCase`.
    """

    def __init__(self, fiscal_info_repository: FiscalInfoRepositoryPort) -> None:
        self._fiscal_info_repository = fiscal_info_repository

    async def execute(self, user_id: str) -> list[dict[str, Any]]:
        """Devuelve los regímenes registrados del usuario."""
        regimens = await self._fiscal_info_repository.get_regimens_by_user_id(
            user_id=user_id
        )

        if not regimens:
            has_fiscal_info = await self._fiscal_info_repository.has_fiscal_info(
                user_id=user_id
            )
            if not has_fiscal_info:
                raise NotFoundError("No hay informacion fiscal asociada a tu usuario")

        return [
            {
                "code": regimen["code"],
                "description": regimen["description"],
                "fecha_alta": (
                    str(regimen["fecha_alta"])
                    if regimen.get("fecha_alta") is not None
                    else None
                ),
            }
            for regimen in regimens
        ]
