import warnings
from src.api.routes import webhooks_api_routes
from src.api.routes import http_api_routes
from src.api.middlewares.cors import add_cors_middleware
from fastapi import FastAPI
from fastapi.responses import JSONResponse

warnings.filterwarnings("ignore", category=UserWarning)

app = FastAPI(
    title="AI Chat API",
    docs_url="/docs",
    description="ChatBot de servicio al cliente con base de conocimiento",
    version="1.0.0",
)


add_cors_middleware(app)


@app.get("/")
async def root():
    return JSONResponse(
        status_code=200,
        content={"status": 200, "message": "Funcionando"},
    )


# webhooks
app.include_router(
    webhooks_api_routes.router,
)

# http_api
app.include_router(
    http_api_routes.router,
)

