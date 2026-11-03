from src.domain.entities.authenticated_user import AuthenticatedUser
from src.domain.ports.repositories.user_repository_port import UserRepositoryPort


class EnsureUserExistsUseCase:
    """Garantiza que el usuario autenticado exista en la tabla `users`.

    La fuente de verdad de los usuarios es Clerk; esta tabla es un espejo
    local que se puebla de forma perezosa en la primera petición autenticada.
    """

    def __init__(self, users_repository: UserRepositoryPort) -> None:
        self._users_repository = users_repository

    async def execute(self, user: AuthenticatedUser) -> None:
        # `insert_if_new` es idempotente: evita el check-then-insert (TOCTOU)
        # cuando llegan peticiones concurrentes del mismo usuario nuevo.
        await self._users_repository.insert_if_new(user)
