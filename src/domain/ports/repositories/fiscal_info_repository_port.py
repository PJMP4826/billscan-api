from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class FiscalInfoRepositoryPort(ABC):
    """Puerto (interfaz) para el manejo de información fiscal y regímenes.

    Define el contrato que cualquier adaptador de infraestructura
    (ej. SQL, NoSQL, Mock para testing) debe implementar.
    """

    @abstractmethod
    async def insert_fiscal_info(
        self,
        user_id: str,
        rfc: str,
        razon_social: str,
        email: str,
        cp: str,
        address: str | None,
        use_cfdi_code_default: str,
    ) -> int:
        """Inserta la información fiscal base del usuario y devuelve su ID."""
        pass

    @abstractmethod
    async def add_regimen(
        self,
        fiscal_info_id: int,
        regimen_code: str,
        regimen_description: str,
        fecha_alta: date,
    ) -> int:
        """Agrega un nuevo régimen fiscal al historial del usuario."""
        pass

    @abstractmethod
    async def get_latest_by_user_id(self, user_id: str) -> dict[str, Any]:
        """Obtiene la información fiscal del usuario junto con su último régimen vigente."""
        pass

    @abstractmethod
    async def get_regimens_by_user_id(self, user_id: str) -> list[dict[str, Any]]:
        """Obtiene todos los regímenes fiscales registrados del usuario.

        Se toman los regímenes asociados a la información fiscal más reciente
        del usuario, sin duplicados por ``regimen_code`` y ordenados por
        ``fecha_alta`` descendente. Cada elemento tiene la forma
        ``{"code": str, "description": str, "fecha_alta": date | None}``.
        """
        pass

    @abstractmethod
    async def has_fiscal_info(self, user_id: str) -> bool:
        """Verifica si un usuario ya tiene información fiscal registrada."""
        pass

    @abstractmethod
    async def update_fiscal_info_details(
        self,
        fiscal_info_id: int,
        rfc: str,
        razon_social: str,
        email: str,
        cp: str,
        address: str | None,
        use_cfdi_code_default: str,
    ) -> None:
        """Actualiza los datos estáticos de la información fiscal."""
        pass
