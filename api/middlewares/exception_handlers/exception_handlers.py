from http import HTTPStatus
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.config.logger import logger
from src.shared.errors.base_exception import BaseAppException


def _title_for_status(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "Error"


def _error_response(
    *,
    status_code: int,
    message: Any,
    error_code: str,
    details: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "title": _title_for_status(status_code),
            "status": status_code,
            "error_code": error_code,
            "message": message,
            "details": details or {},
        },
        headers=headers,
    )


def register_http_exception_handler(app: FastAPI):
    @app.exception_handler(BaseAppException)
    async def custom_app_exception_handler(
        request: Request,
        exc: BaseAppException,
    ):  # type: ignore
        if exc.http_status >= 500:
            logger.exception(
                "Error no público en %s %s: [%s] %s",
                request.method,
                request.url.path,
                exc.error_code,
                exc.get_message(),
            )
        else:
            logger.warning(
                "Error controlado en %s %s: [%s] %s",
                request.method,
                request.url.path,
                exc.error_code,
                exc.get_message(),
            )

        headers = (
            {"WWW-Authenticate": "Bearer"}
            if exc.http_status == 401
            else None
        )

        return JSONResponse(
            status_code=exc.http_status,
            content=exc.to_http_dict(),
            headers=headers,
        )

    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(
        request: Request,
        exc: HTTPException,
    ):  # type: ignore
        detail = exc.detail

        if isinstance(detail, dict):
            message = ( # type: ignore
                detail.get("message") # type: ignore
                or detail.get("detail") # type: ignore
                or str(detail)
            )
            error_code = str(detail.get("error_code") or "HTTP_ERROR") # type: ignore
            details = detail.get("details") or {} # type: ignore
        else:
            message = detail
            error_code = "HTTP_ERROR"
            details = {}

        return _error_response(
            status_code=exc.status_code,
            message=message,
            error_code=error_code,
            details=details, # type: ignore
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def custom_request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):  # type: ignore
        message = "; ".join(error["msg"] for error in exc.errors())
        errors = [ # type: ignore
            {
                "loc": list(error.get("loc", [])),
                "msg": error.get("msg"),
                "type": error.get("type"),
            }
            for error in exc.errors()
        ]

        return _error_response(
            status_code=400,
            message=message,
            error_code="VALIDATION_ERROR",
            details={"errors": errors},
        )

    @app.exception_handler(Exception)
    async def custom_unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ):  # type: ignore
        logger.exception(
            "Excepción no controlada en %s %s",
            request.method,
            request.url.path,
        )

        return _error_response(
            status_code=500,
            message="Ocurrió un error interno.",
            error_code="INTERNAL_SERVER_ERROR",
        )
