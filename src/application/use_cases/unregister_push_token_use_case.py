from src.domain.ports.repositories.push_token_repository_port import (
    PushTokenRepositoryPort,
)
from src.domain.value_objects.user_id import UserId


class UnregisterPushTokenUseCase:
    """Desregistra un token del usuario autenticado (idempotente)."""

    def __init__(self, push_token_repository: PushTokenRepositoryPort) -> None:
        self._push_token_repository = push_token_repository

    async def execute(self, user_id: UserId, token: str) -> None:
        await self._push_token_repository.delete_by_token_and_user_id(
            token=token, user_id=user_id.value
        )
