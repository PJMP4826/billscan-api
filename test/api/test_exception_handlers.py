import asyncio
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException

from api.middlewares.exception_handlers.exception_handlers import (
    register_http_exception_handler,
)
from src.domain.errors.authentication_error import AuthenticationError
from src.domain.errors.receipt_error import ReceiptNotFoundError
from src.domain.errors.reporting_error import InvalidReportingPeriodError
from src.shared.errors.base_exception import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)
from src.shared.errors.billing_exceptions import (
    BillingProviderError,
    BillingWebhookParseError,
    BillingWebhookSignatureError,
)
from src.shared.errors.infrastructure_exceptions import (
    HttpException,
    InfrastructureException,
    PostgresDBException,
)


def _build_app() -> FastAPI:
    app = FastAPI()
    register_http_exception_handler(app)

    @app.get("/bad-request")
    async def bad_request() -> None:
        raise BadRequestError(
            "Dato inválido",
            error_code="TEST_BAD_REQUEST",
            details={"field": "email"},
        )

    @app.get("/not-found")
    async def not_found() -> None:
        raise ReceiptNotFoundError()

    @app.get("/auth")
    async def auth() -> None:
        raise AuthenticationError("Token inválido o expirado")

    @app.get("/invalid-period")
    async def invalid_period() -> None:
        raise InvalidReportingPeriodError(
            "Periodo inválido: 'week'",
            details={"period": "week"},
        )

    @app.get("/infra")
    async def infra() -> None:
        raise InfrastructureException(
            "No se pudo conectar a la base de datos",
            error_code="TEST_INFRA",
            details={"password": "secret"},
        )

    @app.get("/unexpected")
    async def unexpected() -> None:
        raise RuntimeError("stack trace secreto")

    @app.get("/http-error")
    async def http_error() -> None:
        raise HTTPException(
            status_code=403,
            detail="No autorizado",
            headers={"X-Test": "1"},
        )

    @app.get("/validation")
    async def validation(q: int) -> dict[str, int]:
        return {"q": q}

    return app


def _get(app: FastAPI, path: str) -> httpx.Response:
    async def _call() -> httpx.Response:
        transport = httpx.ASGITransport(
            app=app,
            raise_app_exceptions=False,
        )
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.get(path)

    return asyncio.run(_call())


def _assert_envelope(body: dict[str, Any]) -> None:
    assert set(body) == {"title", "status", "error_code", "message", "details"}


def test_bad_request_is_public_and_keeps_details() -> None:
    response = _get(_build_app(), "/bad-request")

    assert response.status_code == 400
    body = response.json()
    _assert_envelope(body)
    assert body == {
        "title": "Bad Request",
        "status": 400,
        "error_code": "TEST_BAD_REQUEST",
        "message": "Dato inválido",
        "details": {"field": "email"},
    }


def test_not_found_uses_resource_error_code() -> None:
    response = _get(_build_app(), "/not-found")

    assert response.status_code == 404
    body = response.json()
    _assert_envelope(body)
    assert body["error_code"] == "RECEIPT_NOT_FOUND"
    assert body["message"] == "Ticket no encontrado"
    assert body["title"] == "Not Found"


def test_authentication_error_returns_www_authenticate_header() -> None:
    response = _get(_build_app(), "/auth")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    body = response.json()
    _assert_envelope(body)
    assert body["error_code"] == "AUTHENTICATION_ERROR"
    assert body["message"] == "Token inválido o expirado"


def test_invalid_period_is_bad_request() -> None:
    response = _get(_build_app(), "/invalid-period")

    assert response.status_code == 400
    body = response.json()
    assert body["error_code"] == "INVALID_REPORTING_PERIOD"
    assert body["details"] == {"period": "week"}


def test_infrastructure_error_hides_message_and_details() -> None:
    response = _get(_build_app(), "/infra")

    assert response.status_code == 500
    body = response.json()
    _assert_envelope(body)
    assert body["error_code"] == "TEST_INFRA"
    assert body["message"] == "Ocurrió un error interno."
    assert body["details"] == {}


def test_unexpected_error_returns_generic_500() -> None:
    response = _get(_build_app(), "/unexpected")

    assert response.status_code == 500
    body = response.json()
    _assert_envelope(body)
    assert body["error_code"] == "INTERNAL_SERVER_ERROR"
    assert body["message"] == "Ocurrió un error interno."
    assert body["details"] == {}


def test_http_exception_uses_standard_envelope_and_headers() -> None:
    response = _get(_build_app(), "/http-error")

    assert response.status_code == 403
    assert response.headers["X-Test"] == "1"
    body = response.json()
    _assert_envelope(body)
    assert body["error_code"] == "HTTP_ERROR"
    assert body["message"] == "No autorizado"


def test_request_validation_error_uses_standard_envelope() -> None:
    response = _get(_build_app(), "/validation?q=not-an-int")

    assert response.status_code == 400
    body = response.json()
    _assert_envelope(body)
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["details"]["errors"]


def test_exception_status_mapping() -> None:
    assert BadRequestError("x").http_status == 400
    assert NotFoundError("x").http_status == 404
    assert ConflictError("x").http_status == 409
    assert AuthenticationError("x").http_status == 401
    assert InvalidReportingPeriodError("x").http_status == 400
    assert ReceiptNotFoundError().http_status == 404
    assert InfrastructureException("x").http_status == 500
    assert PostgresDBException("x").http_status == 500
    assert HttpException("x", url="http://x", method="GET").http_status == 502
    assert BillingProviderError("x").http_status == 502
    assert BillingWebhookSignatureError("x").http_status == 401
    assert BillingWebhookParseError("x").http_status == 400
