from typing import Any

import httpx

from src.config.logger import logger
from src.shared.errors.infrastructure_exceptions import (
    InfrastructureException,
    HttpException,
)
from src.domain.value_objects.image_record import ImageRecord


class HttpClientAdapter:
    def __init__(
        self,
        default_timeout: float = 40.0,
        max_connections: int = 20,
        max_keepalive_connections: int = 10,
    ) -> None:
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )
        self._client = httpx.AsyncClient(
            timeout=default_timeout,
            limits=limits,
        )

    async def get_image(
        self,
        url: str,
        timeout: float | None = None,
    ) -> ImageRecord:
        try:

            response = await self._client.get(
                url=url,
                timeout=timeout,
            )

            image_bytes = response.content
            mime_type = response.headers.get("Content-Type", "image/jpeg")

            return ImageRecord(image_bytes=image_bytes, mime_type=mime_type)

        except Exception as e:
            raise e

    async def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        try:
            response = await self._client.get(
                url=url,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict):
                raise InfrastructureException(
                    "Respuesta JSON invalida: se esperaba un objeto"
                )

            return data  # type: ignore

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code if e.response else None
            body = e.response.text if e.response is not None else ""  # type: ignore
            logger.error(
                "HTTP error en GET %s - status=%s body=%s",
                url,
                status_code if status_code is not None else "unknown",
                body,
            )
            raise HttpException(
                f"HTTP error en GET {url}: status={status_code if status_code is not None else 'unknown'}",
                url=url,
                method="GET",
                upstream_status_code=status_code,
                response_body=body,
            )

        except Exception as e:
            logger.error("Error inesperado en GET %s: %s", url, str(e))
            raise InfrastructureException(f"Error inesperado al llamar {url}: {str(e)}")

    async def close(self) -> None:
        await self._client.aclose()
