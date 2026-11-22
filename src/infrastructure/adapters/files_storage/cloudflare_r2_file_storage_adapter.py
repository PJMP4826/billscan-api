import asyncio
import random

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from botocore.config import Config

from src.domain.ports.file_storage_port import FileStoragePort
from src.config.logger import logger
from src.shared.errors.infrastructure_exceptions import InfrastructureException

_RETRYABLE_ERROR_CODES = frozenset(
    {
        "InternalError",
        "ServiceUnavailable",
        "SlowDown",
        "RequestTimeout",
        "RequestTimeoutException",
        "Throttling",
        "ThrottlingException",
        "TooManyRequestsException",
        "500",
        "502",
        "503",
        "504",
    }
)


def _is_retryable_client_error(exc: ClientError) -> bool:
    response = exc.response or {}
    error = response.get("Error", {}) or {}
    code = str(error.get("Code", ""))
    status = (response.get("ResponseMetadata", {}) or {}).get("HTTPStatusCode")
    return code in _RETRYABLE_ERROR_CODES or (
        isinstance(status, int) and status >= 500
    )


class CloudFlareR2FileStorageAdapter(FileStoragePort):
    """
    Cloudflare R2 adapter using the AWS S3-compatible SDK (boto3).
    R2 is S3-compatible — the only differences are:
      - endpoint_url points to your R2 account endpoint
      - region_name must be "auto"
      - No egress fees

    R2 puede devolver `InternalError` (HTTP 5xx) de forma intermitente, por eso
    el cliente de boto3 reintenta y además hacemos una capa propia de reintentos
    con backoff + jitter.
    """

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        public_base_url: str | None = None,
        max_attempts: int = 3,
        retry_base_delay: float = 0.5,
        retry_max_delay: float = 5.0,
        connect_timeout: float = 10.0,
        read_timeout: float = 60.0,
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
        :param max_attempts:      Intentos propios ante errores transitorios.
        :param retry_base_delay:  Delay inicial del backoff (segundos).
        :param retry_max_delay:   Delay máximo del backoff (segundos).
        :param connect_timeout:   Timeout de conexión TCP (segundos).
        :param read_timeout:      Timeout de lectura (segundos).
        """
        self._bucket = bucket_name
        self._public_base_url = public_base_url.rstrip("/") if public_base_url else None
        self._max_attempts = max(1, max_attempts)
        self._retry_base_delay = max(0.0, retry_base_delay)
        self._retry_max_delay = max(self._retry_base_delay, retry_max_delay)

        self._client = boto3.client(  # type: ignore
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
            config=Config(
                signature_version="s3v4",
                # R2 responde InternalError a algunos requests con checksums
                # flexibles (aws-chunked / x-amz-checksum-mode) cuando el
                # cliente los envía "cuando el servicio lo soporte".
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
                retries={"mode": "standard", "max_attempts": 3},
                connect_timeout=connect_timeout,
                read_timeout=read_timeout,
            ),
        )

    @staticmethod
    def _response_details(exc: ClientError | BotoCoreError) -> dict[str, object]:
        response = getattr(exc, "response", None) or {}
        error = response.get("Error", {}) or {}
        metadata = response.get("ResponseMetadata", {}) or {}
        headers = metadata.get("HTTPHeaders", {}) or {}
        details: dict[str, object] = {}
        if error.get("Code") is not None:
            details["r2_error_code"] = error.get("Code")
        if error.get("Message") is not None:
            details["r2_error_message"] = error.get("Message")
        if metadata.get("HTTPStatusCode") is not None:
            details["upstream_status_code"] = metadata.get("HTTPStatusCode")
        if headers.get("cf-ray") is not None:
            details["cf_ray"] = headers.get("cf-ray")
        return details

    def _log_failure(
        self, operation: str, key: str, exc: ClientError | BotoCoreError
    ) -> None:
        details = self._response_details(exc)
        logger.error(
            "R2 %s failed for key '%s': code=%s status=%s cf_ray=%s message=%s",
            operation,
            key,
            details.get("r2_error_code", "-"),
            details.get("upstream_status_code", "-"),
            details.get("cf_ray", "-"),
            details.get("r2_error_message", str(exc)),
        )

    def _retry_delay(self, attempt: int) -> float:
        delay = min(
            self._retry_max_delay,
            self._retry_base_delay * (2 ** (attempt - 1)),
        )
        return delay + random.uniform(0, delay * 0.25)

    async def _call_with_retries(
        self,
        operation: str,
        func,
        *,
        log_key: str,
        **kwargs,
    ):
        last_exc: ClientError | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                return await asyncio.to_thread(func, **kwargs)
            except ClientError as exc:
                last_exc = exc
                if (
                    not _is_retryable_client_error(exc)
                    or attempt == self._max_attempts
                ):
                    raise
                delay = self._retry_delay(attempt)
                logger.warning(
                    "R2 %s transient error for key '%s' (attempt %d/%d): %s. "
                    "Reintentando en %.2fs",
                    operation,
                    log_key,
                    attempt,
                    self._max_attempts,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
        assert last_exc is not None
        raise last_exc

    async def upload(self, key: str, data: bytes, mime_type: str) -> str:
        """
        Upload raw bytes to R2 and return the storage key.
        """
        try:
            await self._call_with_retries(
                "upload",
                self._client.put_object,
                log_key=key,
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
            self._log_failure("upload", key, e)
            raise InfrastructureException(
                f"R2 upload failed for key '{key}'",
                error_code="R2_UPLOAD_ERROR",
                details={
                    "key": key,
                    "bucket": self._bucket,
                    **self._response_details(e),
                },
                retryable=_is_retryable_client_error(e),
            ) from e
        except BotoCoreError as e:
            self._log_failure("upload", key, e)
            raise InfrastructureException(
                f"R2 upload failed for key '{key}'",
                error_code="R2_UPLOAD_ERROR",
                details={"key": key, "bucket": self._bucket},
                retryable=True,
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
                details={
                    "key": key,
                    "bucket": self._bucket,
                    "expires_in": expires_in,
                    **self._response_details(e),
                },
                retryable=_is_retryable_client_error(e),
            ) from e

    def _download_sync(self, key: str) -> tuple[bytes, str]:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        body = response["Body"]
        try:
            data = body.read()
        finally:
            body.close()
        content_type = response.get("ContentType", "application/octet-stream")
        return data, content_type

    async def download(self, key: str) -> tuple[bytes, str]:
        """
        Download object content and its content-type from R2.
        Returns (data, content_type).
        The backend streams this to the client — no URL is exposed.
        """
        try:
            data, content_type = await self._call_with_retries(
                "download", self._download_sync, log_key=key, key=key
            )
            logger.info("Downloaded object '%s' from bucket '%s'", key, self._bucket)
            return data, content_type
        except ClientError as e:
            self._log_failure("download", key, e)
            raise InfrastructureException(
                f"R2 download failed for key '{key}'",
                error_code="R2_DOWNLOAD_ERROR",
                details={
                    "key": key,
                    "bucket": self._bucket,
                    **self._response_details(e),
                },
                retryable=_is_retryable_client_error(e),
            ) from e
        except BotoCoreError as e:
            self._log_failure("download", key, e)
            raise InfrastructureException(
                f"R2 download failed for key '{key}'",
                error_code="R2_DOWNLOAD_ERROR",
                details={"key": key, "bucket": self._bucket},
                retryable=True,
            ) from e

    async def delete(self, key: str) -> None:
        try:
            await self._call_with_retries(
                "delete",
                self._client.delete_object,  # type: ignore
                log_key=key,
                Bucket=self._bucket,
                Key=key,
            )
            logger.info("Deleted object '%s' from bucket '%s'", key, self._bucket)
        except ClientError as e:
            self._log_failure("delete", key, e)
            raise InfrastructureException(
                f"R2 delete failed for key '{key}'",
                error_code="R2_DELETE_ERROR",
                details={
                    "key": key,
                    "bucket": self._bucket,
                    **self._response_details(e),
                },
                retryable=_is_retryable_client_error(e),
            ) from e
        except BotoCoreError as e:
            self._log_failure("delete", key, e)
            raise InfrastructureException(
                f"R2 delete failed for key '{key}'",
                error_code="R2_DELETE_ERROR",
                details={"key": key, "bucket": self._bucket},
                retryable=True,
            ) from e

    async def exists(self, key: str) -> bool:
        try:
            await self._call_with_retries(
                "exists",
                self._client.head_object,
                log_key=key,
                Bucket=self._bucket,
                Key=key,
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":  # type: ignore
                return False
            self._log_failure("exists", key, e)
            raise InfrastructureException(
                f"R2 exists check failed for key '{key}'",
                error_code="R2_EXISTS_ERROR",
                details={
                    "key": key,
                    "bucket": self._bucket,
                    **self._response_details(e),
                },
                retryable=_is_retryable_client_error(e),
            ) from e
        except BotoCoreError as e:
            self._log_failure("exists", key, e)
            raise InfrastructureException(
                f"R2 exists check failed for key '{key}'",
                error_code="R2_EXISTS_ERROR",
                details={"key": key, "bucket": self._bucket},
                retryable=True,
            ) from e
