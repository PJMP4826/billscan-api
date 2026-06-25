from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.bootstraps.services.infrastructure_bootstrap_services import (
    get_facturagpt_billing_adapter,
)

_facturagpt_adapter_instance = get_facturagpt_billing_adapter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifespan (startup and shutdown) of the FastAPI application.
    """

    await _facturagpt_adapter_instance.startup()

    yield  # Aquí es donde la aplicación FastAPI corre y atiende peticiones

    await _facturagpt_adapter_instance.shutdown()
