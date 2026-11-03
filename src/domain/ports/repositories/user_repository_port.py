from abc import ABC, abstractmethod
from typing import Any

from src.domain.entities.authenticated_user import AuthenticatedUser


class UserRepositoryPort(ABC):
    """Puerto de `users` (espejo local de los usuarios creados en Clerk).

    No existe una entidad propia de la tabla: la fila refleja la entidad de
    dominio `AuthenticatedUser`, por eso las escrituras reciben esa entidad.
    """

    @abstractmethod
    async def insert_if_new(self, user: AuthenticatedUser) -> bool:
        """Inserta el usuario si no existe y devuelve si lo creó.

        Debe ser idempotente (``ON CONFLICT DO NOTHING``) para soportar
        peticiones concurrentes del mismo usuario sin violar constraints.
        """
        pass

    @abstractmethod
    async def find_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Devuelve la fila del usuario o ``None`` si no existe."""
        pass
