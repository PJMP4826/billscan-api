import asyncio

from src.application.use_cases.unregister_push_token_use_case import (
    UnregisterPushTokenUseCase,
)
from src.domain.enums.push_platform import PushPlatform
from src.domain.ports.repositories.push_token_repository_port import (
    PushTokenRepositoryPort,
)
from src.domain.value_objects.user_id import UserId


class _FakePushTokenRepository(PushTokenRepositoryPort):
    def __init__(self) -> None:
        self.upserts: list[tuple[str, str, PushPlatform]] = []
        self.deletes: list[tuple[str, str]] = []

    async def upsert(
        self, user_id: str, token: str, platform: PushPlatform
    ) -> None:
        self.upserts.append((user_id, token, platform))

    async def delete_by_token_and_user_id(self, token: str, user_id: str) -> None:
        self.deletes.append((token, user_id))

    async def find_tokens_by_user_id(self, user_id: str) -> list[str]:
        return []


def test_execute_deletes_token_scoped_to_authenticated_user() -> None:
    repository = _FakePushTokenRepository()
    use_case = UnregisterPushTokenUseCase(push_token_repository=repository)

    asyncio.run(
        use_case.execute(
            user_id=UserId("user_123"),
            token="ExponentPushToken[abc]",
        )
    )

    assert repository.deletes == [("ExponentPushToken[abc]", "user_123")]
    assert repository.upserts == []
