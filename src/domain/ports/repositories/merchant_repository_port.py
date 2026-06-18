from abc import ABC, abstractmethod
from typing import Any

from src.domain.value_objects.merchant_data import MerchantData


class MerchantRepositoryPort(ABC):
    """Puerto (interfaz abstracta) para el repositorio de la tabla `merchants`.

    Mapea hacia/desde el value object `MerchantData`. La tabla tiene una
    restricción UNIQUE compuesta (tax_id, branch_id), por lo que se ofrece
    `find_or_create` para evitar duplicados cuando varias sucursales
    comparten RFC.
    """

    @abstractmethod
    async def insert(self, merchant: MerchantData) -> int:
        """Inserta un comercio y devuelve el `id` (BIGSERIAL) generado."""
        pass

    @abstractmethod
    async def find_by_id(self, merchant_id: int) -> MerchantData | None:
        """Busca un comercio por su ID y devuelve su Value Object."""
        pass

    @abstractmethod
    async def find_by_tax_id_and_branch(
        self, tax_id: str | None, branch_id: str | None
    ) -> dict[str, Any] | None:
        """Busca por la llave única compuesta (tax_id, branch_id).

        Devuelve el dict con `id` incluido (útil para las FKs).
        """
        pass

    @abstractmethod
    async def find_or_create(self, merchant: MerchantData) -> int:
        """Busca un comercio por (tax_id, branch_id); si no existe lo inserta.

        Devuelve el `id` (BIGSERIAL) en cualquier caso.
        """
        pass
