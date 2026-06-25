from abc import ABC, abstractmethod
from typing import Any

from src.domain.entities.receipt import Receipt


class ReceiptRepositoryPort(ABC):
    """Puerto (interfaz abstracta) para el repositorio de la tabla `receipts`.

    NOTA - reconstrucción de entidades:
    Los métodos de lectura (`find_by_id`, `find_by_uuid`) devuelven
    `dict[str, Any]` crudos, NO instancias de `Receipt`. Reconstruir un
    `Receipt` válido requiere también `items`, `taxes`, `payment` y
    `billing` desde sus respectivos repositorios (Receipt.__post_init__
    exige items no vacíos). Esa composición es responsabilidad de la capa
    de orquestación (caso de uso / servicio de aplicación).
    """

    @abstractmethod
    async def insert(
        self,
        receipt: Receipt,
        merchant_id: int | None,
        user_id: str | None,
    ) -> int:
        """Inserta la cabecera del recibo y devuelve el `id` creado."""
        pass

    @abstractmethod
    async def find_by_id(self, receipt_id: int) -> dict[str, Any]:
        """Busca la cabecera de un recibo por su ID interno."""
        pass

    @abstractmethod
    async def find_by_uuid(self, receipt_uuid: str) -> dict[str, Any] | None:
        """Busca la cabecera de un recibo por su UUID público."""
        pass

    @abstractmethod
    async def find_by_user_id(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Lista las cabeceras de los recibos de un usuario, más recientes primero."""
        pass

    @abstractmethod
    async def update_merchant_and_payment(
        self,
        receipt_id: int,
        merchant_id: int | None,
        payment_method_code: str,
    ) -> None:
        """Actualiza las relaciones de comercio y método de pago de un recibo."""
        pass

    @abstractmethod
    async def delete(self, receipt_id: int) -> None:
        """Elimina un recibo por su ID."""
        pass