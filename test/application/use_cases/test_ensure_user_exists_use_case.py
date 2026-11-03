import asyncio
from typing import Any

from src.application.use_cases.ensure_user_exists_use_case import (
    EnsureUserExistsUseCase,
)
from src.domain.entities.authenticated_user import AuthenticatedUser
from src.domain.ports.repositories.user_repository_port import UserRepositoryPort
from src.domain.value_objects.user_id import UserId


class _FakeUserRepository(UserRepositoryPort):
    def __init__(self) -> None:
        self.calls: list[AuthenticatedUser] = []
        self.existing: set[str] = set()

    async def insert_if_new(self, user: AuthenticatedUser) -> bool:
        self.calls.append(user)
        if user.user_id.value in self.existing:
            return False
        self.existing.add(user.user_id.value)
        return True

    async def find_by_id(self, user_id: str) -> dict[str, Any] | None:
        return {"id": user_id, "email": ""} if user_id in self.existing else None


def test_execute_calls_insert_if_new_and_is_idempotent() -> None:
    repository = _FakeUserRepository()
    use_case = EnsureUserExistsUseCase(users_repository=repository)
    user = AuthenticatedUser(user_id=UserId("user_1"), email="user@example.com")

    asyncio.run(use_case.execute(user))
    asyncio.run(use_case.execute(user))

    # El caso de uso siempre delega: la idempotencia vive en el repositorio
    # (`ON CONFLICT DO NOTHING`), evitando el check-then-insert.
    assert repository.calls == [user, user]
    assert repository.existing == {"user_1"}
