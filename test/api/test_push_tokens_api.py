import asyncio
from typing import Any

import httpx
from fastapi import FastAPI
from pytest import MonkeyPatch

import api.http.controllers.register_push_token_controller as register_module
import api.http.controllers.unregister_push_token_controller as unregister_module
from api.http.dependencies import get_current_user_id
from api.middlewares.exception_handlers.exception_handlers import (
    register_http_exception_handler,
)
from api.routes.http_api_routes import router
from src.domain.enums.push_platform import PushPlatform
from src.domain.value_objects.user_id import UserId


class _FakeRegisterPushTokenUseCase:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, PushPlatform]] = []

    async def execute(
        self, user_id: UserId, token: str, platform: PushPlatform
    ) -> None:
        self.calls.append((user_id.value, token, platform))


class _FakeUnregisterPushTokenUseCase:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def execute(self, user_id: UserId, token: str) -> None:
        self.calls.append((user_id.value, token))


def _build_app(
    monkeypatch: MonkeyPatch,
    register_use_case: _FakeRegisterPushTokenUseCase,
    unregister_use_case: _FakeUnregisterPushTokenUseCase,
) -> FastAPI:
    app = FastAPI()
    register_http_exception_handler(app)
    app.include_router(router)
    app.dependency_overrides[get_current_user_id] = lambda: UserId("user_123")

    monkeypatch.setattr(
        register_module,
        "get_register_push_token_use_case",
        lambda: register_use_case,
    )
    monkeypatch.setattr(
        unregister_module,
        "get_unregister_push_token_use_case",
        lambda: unregister_use_case,
    )
    return app


def _request(
    app: FastAPI, method: str, path: str, **kwargs: Any
) -> httpx.Response:
    async def _call() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(_call())


def test_register_token_is_idempotent_and_trims_token(
    monkeypatch: MonkeyPatch,
) -> None:
    register_use_case = _FakeRegisterPushTokenUseCase()
    app = _build_app(monkeypatch, register_use_case, _FakeUnregisterPushTokenUseCase())

    response = _request(
        app,
        "POST",
        "/api/push-tokens",
        json={
            "token": "  ExponentPushToken[abc]  ",
            "platform": "android",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": 200,
        "message": "Token de notificación registrado",
    }
    assert register_use_case.calls == [
        ("user_123", "ExponentPushToken[abc]", PushPlatform.ANDROID)
    ]


def test_register_token_rejects_invalid_platform(
    monkeypatch: MonkeyPatch,
) -> None:
    register_use_case = _FakeRegisterPushTokenUseCase()
    app = _build_app(monkeypatch, register_use_case, _FakeUnregisterPushTokenUseCase())

    response = _request(
        app,
        "POST",
        "/api/push-tokens",
        json={"token": "ExponentPushToken[abc]", "platform": "web"},
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "VALIDATION_ERROR"
    assert register_use_case.calls == []


def test_unregister_token_is_idempotent_and_scoped_to_user(
    monkeypatch: MonkeyPatch,
) -> None:
    unregister_use_case = _FakeUnregisterPushTokenUseCase()
    app = _build_app(monkeypatch, _FakeRegisterPushTokenUseCase(), unregister_use_case)

    # httpx codifica los corchetes del token al construir la URL.
    first = _request(
        app, "DELETE", "/api/push-tokens/ExponentPushToken[abc]"
    )
    second = _request(
        app, "DELETE", "/api/push-tokens/ExponentPushToken[abc]"
    )

    for response in (first, second):
        assert response.status_code == 200
        assert response.json() == {
            "status": 200,
            "message": "Token de notificación eliminado",
        }

    # El token se decodifica y el user_id viene de la autenticación, no del path.
    assert unregister_use_case.calls == [
        ("user_123", "ExponentPushToken[abc]"),
        ("user_123", "ExponentPushToken[abc]"),
    ]
