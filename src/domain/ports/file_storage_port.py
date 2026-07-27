from abc import ABC, abstractmethod


class FileStoragePort(ABC):
    """
    Port that defines the contract every file storage adapter must fulfill.
    All adapters (R2, S3, GCS, local disk) must implement these methods.
    """

    @abstractmethod
    async def upload(self, key: str, data: bytes, mime_type: str) -> str:
        """
        Upload a file and return its storage key.

        :param key:       Storage key / path (e.g. "users/fausto/ticket-123.jpg")
        :param data:      Raw file bytes
        :param mime_type: MIME type (e.g. "image/jpeg", "image/png")
        :return:          Storage key string (NOT a URL)
        """
        ...

    @abstractmethod
    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for an existing object.

        :param key:        Storage key of the object
        :param expires_in: Seconds until the URL expires (default: 1 hour)
        :return:           Presigned URL string
        """
        ...

    @abstractmethod
    async def download(self, key: str) -> tuple[bytes, str]:
        """
        Download object content and its content-type from storage.

        :param key: Storage key of the object
        :return:    Tuple of (raw bytes, content_type)
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Delete an object from storage.

        :param key: Storage key of the object to delete
        """
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check whether an object exists in storage.

        :param key: Storage key to check
        :return:    True if object exists, False otherwise
        """
        ...
