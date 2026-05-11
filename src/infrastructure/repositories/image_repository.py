import uuid

from src.domain.ports.file_storage_port import FileStoragePort
from src.infrastructure.records.uploaded_image import UploadedImage


class ImageRepository:
    """
    Repository responsible for image persistence.
    It is decoupled from any specific storage provider via the FileStoragePort.

    Inject any adapter (R2, S3, local) — this class doesn't know or care.
    """

    def __init__(self, storage: FileStoragePort, key_prefix: str = "images") -> None:
        """
        :param storage:    Any adapter implementing FileStoragePort
        :param key_prefix: Folder/prefix for all image keys (e.g. "avatars", "products")
        """
        self._storage = storage
        self._key_prefix = key_prefix.strip("/")

    async def save(
        self,
        data: bytes,
        mime_type: str,
        filename: str | None = None,
    ) -> UploadedImage:
        """
        Upload an image to storage.

        :param data:      Raw image bytes
        :param mime_type: MIME type (e.g. "image/jpeg", "image/webp")
        :param filename:  Optional filename. If None, a UUID is generated.
        :return:          UploadedImage with key and accessible URL
        """
        extension = self._extension_from_mime(mime_type)
        name = filename or f"{uuid.uuid4()}{extension}"
        key = f"{self._key_prefix}/{name}"

        url = await self._storage.upload(key=key, data=data, mime_type=mime_type)

        return UploadedImage(key=key, url=url, mime_type=mime_type)

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Get a (possibly presigned) URL for an existing image key.

        :param key:        Full storage key (e.g. "images/fausto.jpg")
        :param expires_in: Seconds until presigned URL expires
        :return:           URL string
        """
        if not await self._storage.exists(key):
            raise FileNotFoundError(f"Image not found in storage: '{key}'")

        return await self._storage.get_url(key, expires_in=expires_in)

    async def delete(self, key: str) -> None:
        """
        Delete an image by its storage key.
        """
        if not await self._storage.exists(key):
            raise FileNotFoundError(f"Cannot delete — image not found: '{key}'")

        await self._storage.delete(key)

    @staticmethod
    def _extension_from_mime(mime_type: str) -> str:
        mapping = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
            "image/svg+xml": ".svg",
        }
        ext = mapping.get(mime_type)
        if not ext:
            raise ValueError(f"Unsupported image MIME type: '{mime_type}'")
        return ext
