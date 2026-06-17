import asyncio
from pathlib import Path

import aiofiles

from src.domain.ports.file_storage_port import FileStoragePort
from src.config.logger import logger
from src.shared.errors.infrastructure_exceptions import InfrastructureException


class DiskFileStorageAdapter(FileStoragePort):
    def __init__(
        self,
        base_directory: str = "uploads",
        base_url: str = "http://localhost:8000/static",
    ) -> None:
        # resolvemos la ruta absoluta PARA GUARDAR en el disco del servidor
        self._base_directory = Path(base_directory).resolve()

        # guardamos la URL base PARA DEVOLVER a la app mobile
        self._base_url = base_url.rstrip("/")

        self._base_directory.mkdir(parents=True, exist_ok=True)
        logger.info(
            "DiskFileStorageAdapter initialized with base directory: %s and base_url: %s",
            self._base_directory,
            self._base_url,
        )

    async def upload(self, key: str, data: bytes, mime_type: str) -> str:
        file_path = self._base_directory / key
        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(data)

            public_url = f"{self._base_url}/{key}"

            logger.info(
                "Uploaded object '%s' to disk. Public URL: '%s'", key, public_url
            )

            return public_url

        except IOError as e:
            logger.error("Disk upload failed for key '%s': %s", key, e)
            raise InfrastructureException(
                f"File not found for key '{key}'",
                error_code="DISK_FILE_NOT_FOUND",
                details={"key": key, "path": str(file_path)},
            )

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        if await self.exists(key):
            # devolvemos la misma URL publica HTTP
            return f"{self._base_url}/{key}"
        else:
            raise InfrastructureException(
                f"File not found for key '{key}'",
                error_code="DISK_FILE_NOT_FOUND",
                details={"key": key},
            )

    async def delete(self, key: str) -> None:
        file_path = self._base_directory / key
        try:
            if await self.exists(key):
                await asyncio.to_thread(file_path.unlink)
                logger.info("Deleted object '%s' from disk at '%s'", key, file_path)
            else:
                logger.warning(
                    "Attempted to delete non-existent object '%s' from disk", key
                )
        except OSError as e:
            logger.error("Disk delete failed for key '%s': %s", key, e)
            raise InfrastructureException(
                f"Disk delete failed for key '{key}'",
                error_code="DISK_DELETE_ERROR",
                details={"key": key, "path": str(file_path)},
            ) from e

    async def exists(self, key: str) -> bool:
        file_path = self._base_directory / key
        return await asyncio.to_thread(file_path.exists)
