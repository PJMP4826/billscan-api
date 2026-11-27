from abc import ABC, abstractmethod

from src.domain.enums.push_platform import PushPlatform


class PushTokenRepositoryPort(ABC):
    """Puerto de `push_tokens` (tokens de Expo por dispositivo).

    El token es UNIQUE global: un mismo dispositivo puede cambiar de usuario y
    el registro reasigna la fila (gana el último login). El borrado siempre
    está acotado al `user_id` autenticado.
    """

    @abstractmethod
    async def upsert(
        self, user_id: str, token: str, platform: PushPlatform
    ) -> None:
        """Registra o reasigna el token al usuario (idempotente)."""
        pass

    @abstractmethod
    async def delete_by_token_and_user_id(self, token: str, user_id: str) -> None:
        """Borra el token solo si pertenece al usuario. Idempotente si no existe."""
        pass
