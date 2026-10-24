from typing import Any
from src.domain.ports.repositories.fiscal_info_repository_port import (
    FiscalInfoRepositoryPort,
)
from src.shared.errors.base_exception import NotFoundError
from src.domain.ports.data_encryptor import DataEncryptor


class GetUserFiscalInfoUseCase:
    def __init__(
        self, fiscal_info_repository: FiscalInfoRepositoryPort, encryptor: DataEncryptor
    ):
        self._repository = fiscal_info_repository
        self._encryptor = encryptor

    async def execute(self, user_id: str) -> dict[str, Any]:
        """
        Obtiene la información fiscal vigente del usuario.
        Mapea la respuesta cruda del repositorio a una estructura limpia.
        """
        try:
            raw_data = await self._repository.get_latest_by_user_id(user_id)
        except ValueError as e:
            # El repositorio lanza ValueError si no encuentra registros
            raise NotFoundError(str(e)) from e

        # Mapeo seguro (maneja NULLs del LEFT JOIN)
        regimen_data = raw_data.get("regimen_id")

        # Lista completa de regímenes del RFC para que el cliente pueda elegir
        # con cuál facturar (el régimen se envía en la request del ticket).
        raw_regimens = await self._repository.get_regimens_by_user_id(user_id=user_id)

        return {
            "rfc": self._encryptor.decrypt(raw_data["rfc"]),
            "razon_social": self._encryptor.decrypt(raw_data["razon_social"]),
            "email": self._encryptor.decrypt(raw_data["fiscal_email"]),
            "cp": self._encryptor.decrypt(raw_data["cp"]),
            "address": self._encryptor.decrypt(raw_data["address"]),
            "use_cfdi_default": raw_data["use_cfdi_default"],
            "regimen_actual": (
                {
                    "code": raw_data["regimen_code"],
                    "description": raw_data["regimen_description"],
                    "fecha_alta": str(raw_data["fecha_alta"]),
                }
                if regimen_data
                else None
            ),
            "regimenes": [
                {
                    "code": regimen["code"],
                    "description": regimen["description"],
                    "fecha_alta": (
                        str(regimen["fecha_alta"])
                        if regimen.get("fecha_alta") is not None
                        else None
                    ),
                }
                for regimen in raw_regimens
            ],
        }
