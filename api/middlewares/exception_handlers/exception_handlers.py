from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException, FastAPI
from fastapi.exceptions import RequestValidationError

from src.domain.errors.authentication_error import AuthenticationError


def register_http_exception_handler(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request: Request, exc: HTTPException):  # type: ignore
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "title": "Forbidden" if exc.status_code == 403 else "Error",
                "status": exc.status_code,
                "message": exc.detail,
            },
            # Se propagan los headers de la excepción (p. ej. `WWW-Authenticate`
            # en los 401) para no romper el contrato HTTP.
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(AuthenticationError)
    async def custom_authentication_exception_handler(
        request: Request,
        exc: AuthenticationError,
    ):  # type: ignore
        return JSONResponse(
            status_code=401,
            content={
                "title": "Unauthorized",
                "status": 401,
                "message": exc.get_message(),
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(RequestValidationError)
    async def custom_request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):  # type: ignore
        message = "; ".join(error["msg"] for error in exc.errors())

        return JSONResponse(
            status_code=400,
            content={
                "title": "BAD REQUEST",
                "status": 400,
                "message": message,
            },
        )
