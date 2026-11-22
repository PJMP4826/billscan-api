from abc import ABC, abstractmethod
from datetime import date
from typing import Any

RegimenRecord = tuple[str, str, date]


class FiscalInfoRepositoryPort(ABC):
    """Puerto (interfaz) para el manejo de información fiscal y regímenes.

    Define el contrato que cualquier adaptador de infraestructura
    (ej. SQL, NoSQL, Mock para testing) debe implementar.

    La tabla ``fiscal_info`` tiene un registro único por usuario
    (``UNIQUE(user_id)``), por lo que guardar información fiscal es un upsert.
    """

    @abstractmethod
    async def upsert_fiscal_info(
        self,
        user_id: str,
        rfc: str,
        razon_social: str,
        email: str,
        cp: str,
        address: str | None,
        use_cfdi_code_default: str,
    ) -> tuple[int, bool]:
        """Crea o actualiza la información fiscal base del usuario.

        Returns:
            Una tupla ``(id, created)``: el ``id`` del registro y si la fila
            fue insertada (``True``) o actualizada (``False``).
        """
        pass

    @abstractmethod
    async def replace_regimens(
        self,
        fiscal_info_id: int,
        regimens: list[RegimenRecord],
    ) -> None:
        """Reemplaza los regímenes del usuario por los recibidos.

        Cada elemento es ``(regimen_code, regimen_description, fecha_alta)``.
        """
        pass

    @abstractmethod
    async def get_latest_by_user_id(self, user_id: str) -> dict[str, Any]:
        """Obtiene la información fiscal del usuario junto con su último régimen vigente."""
        pass

    @abstractmethod
    async def get_rfc_by_user_id(self, user_id: str) -> str:
        """Obtiene el RFC cifrado de la información fiscal del usuario.

        Raises:
            FiscalInfoNotFoundError: si el usuario no tiene información fiscal
                registrada.
        """
        pass

    @abstractmethod
    async def get_regimens_by_user_id(self, user_id: str) -> list[dict[str, Any]]:
        """Obtiene todos los regímenes fiscales registrados del usuario.

        Se devuelven sin duplicados por ``regimen_code`` y ordenados por
        ``fecha_alta`` descendente. Cada elemento tiene la forma
        ``{"code": str, "description": str, "fecha_alta": date | None}``.
        """
        pass

    @abstractmethod
    async def has_fiscal_info(self, user_id: str) -> bool:
        """Verifica si un usuario ya tiene información fiscal registrada."""
        pass
