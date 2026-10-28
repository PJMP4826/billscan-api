from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException, FastAPI
from fastapi.exceptions import RequestValidationError


def register_http_exception_handler(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request: Request, exc: HTTPException): # type: ignore
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "title": "Forbidden" if exc.status_code == 403 else "Error",
                "status": exc.status_code,
                "message": exc.detail,
            },
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
