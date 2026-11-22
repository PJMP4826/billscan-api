import asyncio
from typing import Any

import pytest
from botocore.exceptions import ClientError

from src.infrastructure.adapters.files_storage import (
    cloudflare_r2_file_storage_adapter as adapter_module,
)
from src.infrastructure.adapters.files_storage.cloudflare_r2_file_storage_adapter import (
    CloudFlareR2FileStorageAdapter,
)
from src.shared.errors.infrastructure_exceptions import InfrastructureException


def _client_error(code: str, status: int) -> ClientError:
    return ClientError(
        {
            "Error": {"Code": code, "Message": "boom"},
            "ResponseMetadata": {
                "HTTPStatusCode": status,
                "HTTPHeaders": {"cf-ray": "ray-123"},
            },
        },
        "PutObject",
    )


class _Body:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self.closed = False

    def read(self) -> bytes:
        return self._data

    def close(self) -> None:
        self.closed = True


class _FakeS3Client:
    def __init__(
        self,
        put_outcomes: list[Any] | None = None,
        get_outcomes: list[Any] | None = None,
    ) -> None:
        self.put_outcomes = list(put_outcomes or [])
        self.get_outcomes = list(get_outcomes or [])
        self.put_calls = 0
        self.get_calls = 0

    def put_object(self, **kwargs: Any) -> dict[str, Any]:
        self.put_calls += 1
        outcome = self.put_outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def get_object(self, **kwargs: Any) -> dict[str, Any]:
        self.get_calls += 1
        outcome = self.get_outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _build_adapter(monkeypatch: pytest.MonkeyPatch, client: _FakeS3Client):
    monkeypatch.setattr(adapter_module.boto3, "client", lambda *a, **k: client)
    return CloudFlareR2FileStorageAdapter(
        account_id="account",
        access_key_id="key",
        secret_access_key="secret",
        bucket_name="bucket",
        max_attempts=3,
        retry_base_delay=0,
    )


def test_upload_retries_transient_internal_errors(monkeypatch):
    client = _FakeS3Client(
        put_outcomes=[
            _client_error("InternalError", 500),
            _client_error("InternalError", 500),
            {},
        ]
    )
    adapter = _build_adapter(monkeypatch, client)

    key = asyncio.run(adapter.upload("key", b"data", "image/jpeg"))

    assert key == "key"
    assert client.put_calls == 3


def test_upload_does_not_retry_non_retryable_errors(monkeypatch):
    client = _FakeS3Client(put_outcomes=[_client_error("AccessDenied", 403)])
    adapter = _build_adapter(monkeypatch, client)

    with pytest.raises(InfrastructureException) as exc_info:
        asyncio.run(adapter.upload("key", b"data", "image/jpeg"))

    assert exc_info.value.error_code == "R2_UPLOAD_ERROR"
    assert exc_info.value.retryable is False
    assert exc_info.value.details["upstream_status_code"] == 403
    assert exc_info.value.details["cf_ray"] == "ray-123"
    assert client.put_calls == 1


def test_upload_raises_after_retries_are_exhausted(monkeypatch):
    client = _FakeS3Client(
        put_outcomes=[_client_error("InternalError", 500) for _ in range(3)]
    )
    adapter = _build_adapter(monkeypatch, client)

    with pytest.raises(InfrastructureException) as exc_info:
        asyncio.run(adapter.upload("key", b"data", "image/jpeg"))

    assert exc_info.value.error_code == "R2_UPLOAD_ERROR"
    assert exc_info.value.retryable is True
    assert client.put_calls == 3


def test_download_retries_transient_errors(monkeypatch):
    client = _FakeS3Client(
        get_outcomes=[
            _client_error("InternalError", 500),
            {"Body": _Body(b"image-bytes"), "ContentType": "image/jpeg"},
        ]
    )
    adapter = _build_adapter(monkeypatch, client)

    data, content_type = asyncio.run(adapter.download("key"))

    assert data == b"image-bytes"
    assert content_type == "image/jpeg"
    assert client.get_calls == 2
