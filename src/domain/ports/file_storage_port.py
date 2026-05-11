from abc import ABC, abstractmethod


class FileStoragePort(ABC):
    """
    Port that defines the contract every file storage adapter must fulfill.
    All adapters (R2, S3, GCS, local disk) must implement these methods.
    """

    @abstractmethod
    def upload(
        self,
        key: str,
        data: bytes,
        mime_type: str,
    ) -> str:
        """
        Upload a file and return its public URL or storage key.

        :param key:       Storage key / path (e.g. "avatars/fausto.jpg")
        :param data:      Raw file bytes
        :param mime_type: MIME type (e.g. "image/jpeg", "image/png", "image/webp")
        :return:          Accessible URL string
        """
        ...

    @abstractmethod
    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for an existing object.

        :param key:        Storage key of the object
        :param expires_in: Seconds until the URL expires (default: 1 hour)
        :return:           Presigned URL string
        """
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Delete an object from storage.

        :param key: Storage key of the object to delete
        """
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check whether an object exists in storage.

        :param key: Storage key to check
        :return:    True if object exists, False otherwise
        """
        ...
