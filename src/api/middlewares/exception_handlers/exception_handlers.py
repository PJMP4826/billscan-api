from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException, FastAPI


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
