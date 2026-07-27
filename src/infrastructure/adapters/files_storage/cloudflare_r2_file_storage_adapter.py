import asyncio

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from src.domain.ports.file_storage_port import FileStoragePort
from src.config.logger import logger
from src.shared.errors.infrastructure_exceptions import InfrastructureException


class CloudFlareR2FileStorageAdapter(FileStoragePort):
    """
    Cloudflare R2 adapter using the AWS S3-compatible SDK (boto3).
    R2 is S3-compatible — the only differences are:
      - endpoint_url points to your R2 account endpoint
      - region_name must be "auto"
      - No egress fees
    """

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        public_base_url: str | None = None,
    ) -> None:
        """
        :param account_id:        Cloudflare account ID
        :param access_key_id:     R2 API token access key
        :param secret_access_key: R2 API token secret key
        :param bucket_name:       Name of the R2 bucket
        :param public_base_url:   Optional public domain for the bucket
                                  (e.g. "https://cdn.yourdomain.com").
                                  If provided, upload() returns a direct public URL.
                                  If None, upload() returns a presigned URL.
        """
        self._bucket = bucket_name
        self._public_base_url = public_base_url.rstrip("/") if public_base_url else None

        self._client = boto3.client(  # type: ignore
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    async def upload(self, key: str, data: bytes, mime_type: str) -> str:
        """
        Upload raw bytes to R2 and return the storage key.
        """
        try:
            await asyncio.to_thread(
                self._client.put_object,
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=mime_type,
            )
            logger.info(
                "Uploaded object '%s' (%s) to bucket '%s'", key, mime_type, self._bucket
            )
            return key
        except ClientError as e:
            logger.error("R2 upload failed for key '%s': %s", key, e)
            raise InfrastructureException(
                f"R2 upload failed for key '{key}'",
                error_code="R2_UPLOAD_ERROR",
                details={"key": key, "bucket": self._bucket},
            ) from e

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned GET URL for a private object.
        """
        try:
            url = await asyncio.to_thread(
                self._client.generate_presigned_url,
                ClientMethod="get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error("Failed to generate presigned URL for key '%s': %s", key, e)
            raise InfrastructureException(
                f"Failed to generate presigned URL for key '{key}'",
                error_code="R2_PRESIGNED_URL_ERROR",
                details={"key": key, "bucket": self._bucket, "expires_in": expires_in},
            ) from e

    async def download(self, key: str) -> tuple[bytes, str]:
        """
        Download object content and its content-type from R2.
        Returns (data, content_type).
        The backend streams this to the client — no URL is exposed.
        """
        try:
            response = await asyncio.to_thread(
                self._client.get_object,
                Bucket=self._bucket,
                Key=key,
            )
            content_type = response.get("ContentType", "application/octet-stream")
            data = await asyncio.to_thread(response["Body"].read)
            logger.info("Downloaded object '%s' from bucket '%s'", key, self._bucket)
            return data, content_type
        except ClientError as e:
            logger.error("R2 download failed for key '%s': %s", key, e)
            raise InfrastructureException(
                f"R2 download failed for key '{key}'",
                error_code="R2_DOWNLOAD_ERROR",
                details={"key": key, "bucket": self._bucket},
            ) from e

    async def delete(self, key: str) -> None:
        try:
            await asyncio.to_thread(
                self._client.delete_object,
                Bucket=self._bucket,
                Key=key,
            )
            logger.info("Deleted object '%s' from bucket '%s'", key, self._bucket)
        except ClientError as e:
            logger.error("R2 delete failed for key '%s': %s", key, e)
            raise InfrastructureException(
                f"R2 delete failed for key '{key}'",
                error_code="R2_DELETE_ERROR",
                details={"key": key, "bucket": self._bucket},
            ) from e

    async def exists(self, key: str) -> bool:
        try:
            await asyncio.to_thread(
                self._client.head_object,
                Bucket=self._bucket,
                Key=key,
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":  # type: ignore
                return False
            logger.error("R2 exists check failed for key '%s': %s", key, e)
            raise InfrastructureException(
                f"R2 exists check failed for key '{key}'",
                error_code="R2_EXISTS_ERROR",
                details={"key": key, "bucket": self._bucket},
            ) from e
