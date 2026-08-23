from abc import ABC, abstractmethod
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
    async def save(
        self,
        receipt: Receipt,
        user_id: str | None,
        merchant_id: int | None,
    ) -> int:
        """Inserta la cabecera del recibo y devuelve el `id` creado."""
        pass

    @abstractmethod
    async def find_by_id(self, receipt_id: int) -> Receipt:
        """Busca la cabecera de un recibo por su ID interno."""
        pass

    @abstractmethod
    async def find_by_uuid(self, receipt_uuid: str) -> Receipt:
        """Busca la cabecera de un recibo por su UUID público."""
        pass

    @abstractmethod
    async def delete(self, receipt_id: int) -> None:
        """Elimina un recibo por su ID."""
        pass