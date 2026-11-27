from src.domain.enums.push_platform import PushPlatform
from src.domain.ports.repositories.push_token_repository_port import (
    PushTokenRepositoryPort,
)
from src.domain.value_objects.user_id import UserId


class RegisterPushTokenUseCase:
    """Registra (o reasigna) el token de notificaciones del dispositivo actual."""

    def __init__(self, push_token_repository: PushTokenRepositoryPort) -> None:
        self._push_token_repository = push_token_repository

    async def execute(
        self, user_id: UserId, token: str, platform: PushPlatform
    ) -> None:
        await self._push_token_repository.upsert(
            user_id=user_id.value, token=token, platform=platform
        )
