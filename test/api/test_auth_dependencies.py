import asyncio

import httpx
from fastapi import Depends, FastAPI

from api.http.dependencies import get_current_user_id
from api.middlewares.exception_handlers.exception_handlers import (
    register_http_exception_handler,
)
from src.application.use_cases.ensure_user_exists_use_case import (
    EnsureUserExistsUseCase,
)
from src.bootstraps.services.infrastructure_bootstrap_services import (
    get_token_verifier_adapter,
)
from src.bootstraps.use_cases_bootstrap import get_ensure_user_use_case
from src.domain.entities.authenticated_user import AuthenticatedUser
from src.domain.errors.authentication_error import AuthenticationError
from src.domain.ports.token_verifier_port import TokenVerifierPort
from src.domain.value_objects.user_id import UserId

_IDENTITY = AuthenticatedUser(user_id=UserId("user_123"), email="user@example.com")


class _FakeVerifier(TokenVerifierPort):
    def __init__(self, identity: AuthenticatedUser | None = None) -> None:
        self._identity = identity

    async def verify(self, bearer_token: str) -> AuthenticatedUser:
        if self._identity is None:
            raise AuthenticationError("Token de sesión inválido o expirado")
        return self._identity


class _FakeEnsureUser(EnsureUserExistsUseCase):
    """Registra la entidad recibida en vez de tocar la base de datos."""

    def __init__(self) -> None:
        self.calls: list[AuthenticatedUser] = []

    async def execute(self, user: AuthenticatedUser) -> None:
        self.calls.append(user)


def _build_app(verifier: TokenVerifierPort) -> tuple[FastAPI, _FakeEnsureUser]:
    """App mínima que monta la dependency real y los handlers reales."""
    app = FastAPI()
    register_http_exception_handler(app)
    ensure_user = _FakeEnsureUser()

    app.dependency_overrides[get_token_verifier_adapter] = lambda: verifier
    app.dependency_overrides[get_ensure_user_use_case] = lambda: ensure_user

    @app.get("/protected")
    async def protected(
        user_id: UserId = Depends(get_current_user_id),
    ) -> dict[str, str]:
        return {"user_id": user_id.value}

    return app, ensure_user


def _get(app: FastAPI, token: str | None) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    async def _call() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.get("/protected", headers=headers)

    return asyncio.run(_call())


def test_requires_bearer_token() -> None:
    app, ensure_user = _build_app(_FakeVerifier(_IDENTITY))

    response = _get(app, token=None)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert ensure_user.calls == []


def test_invalid_token_returns_401_without_leaking_reason() -> None:
    app, ensure_user = _build_app(_FakeVerifier())

    response = _get(app, token="bad-token")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["message"] == "Token inválido o expirado"
    assert ensure_user.calls == []


def test_valid_token_ensures_user_and_injects_user_id() -> None:
    app, ensure_user = _build_app(_FakeVerifier(_IDENTITY))

    response = _get(app, token="good-token")

    assert response.status_code == 200
    assert response.json() == {"user_id": "user_123"}
    assert ensure_user.calls == [_IDENTITY]
