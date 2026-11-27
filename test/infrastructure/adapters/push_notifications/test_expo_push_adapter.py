import asyncio
import gzip
import json
from typing import Any, Callable

import httpx
import pytest

from src.application.dtos.push_notification_dto import PushNotification
from src.domain.enums.push_priority import PushPriority
from src.infrastructure.adapters.push_notifications.expo_push_adapter import (
    ExpoPushNotificationAdapter,
)
from src.shared.errors.notification_exceptions import (
    NotificationBadRequestError,
    NotificationServerError,
    NotificationTimeoutError,
)

Handler = Callable[[httpx.Request], httpx.Response]


def _payload(request: httpx.Request) -> Any:
    body = request.content
    if request.headers.get("Content-Encoding") == "gzip":
        body = gzip.decompress(body)
    return json.loads(body)


def _run(handler: Handler, coro_factory, **adapter_kwargs: Any):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = ExpoPushNotificationAdapter(client=client, **adapter_kwargs)

    async def runner():
        try:
            return await coro_factory(adapter)
        finally:
            await client.aclose()

    return asyncio.run(runner())


def test_send_maps_payload_and_returns_ticket_results():
    captured: list[list[dict[str, Any]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = _payload(request)
        captured.append(payload)
        return httpx.Response(
            200,
            json={"data": [{"status": "ok", "id": f"ticket-{i}"} for i in range(len(payload))]},
        )

    notification = PushNotification(
        title="Factura lista",
        body="Tu factura ya está disponible",
        data={"receipt_id": "abc"},
        priority=PushPriority.HIGH,
        channel_id="billing",
        category_id="invoice",
        icon="ic_bill",
    )

    result = _run(
        handler,
        lambda adapter: adapter.send(notification, ["ExponentPushToken[a]"]),
    )

    assert len(result) == 1
    assert result[0].token == "ExponentPushToken[a]"
    assert result[0].accepted is True
    assert result[0].delivery_id == "ticket-0"
    # Expo recibe un arreglo de mensajes por request.
    message = captured[0][0]
    assert message["to"] == "ExponentPushToken[a]"
    assert message["title"] == "Factura lista"
    assert message["priority"] == "high"
    assert message["channelId"] == "billing"
    assert message["categoryId"] == "invoice"
    assert "ttl" not in message


def test_send_expands_recipients_and_chunks_requests():
    request_sizes: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = _payload(request)
        request_sizes.append(len(payload))
        return httpx.Response(
            200,
            json={"data": [{"status": "ok", "id": f"ticket-{i}"} for i in range(len(payload))]},
        )

    tokens = [f"token-{i}" for i in range(150)]
    result = _run(
        handler,
        lambda adapter: adapter.send(PushNotification(title="x"), tokens),
        max_messages_per_request=100,
    )

    assert request_sizes == [100, 50]
    assert [item.token for item in result] == tokens


def test_ticket_error_is_returned_not_raised():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "status": "error",
                        "message": "Device is not registered",
                        "details": {"error": "DeviceNotRegistered"},
                    }
                ]
            },
        )

    result = _run(
        handler,
        lambda adapter: adapter.send(PushNotification(title="x"), ["token-1"]),
    )

    assert len(result) == 1
    assert result[0].accepted is False
    assert result[0].is_device_not_registered is True
    assert result[0].error_code == "DeviceNotRegistered"


def test_send_retries_rate_limit_and_succeeds():
    attempts: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(request)
        if len(attempts) == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "0"},
                json={"errors": [{"code": "TOO_MANY_REQUESTS", "message": "slow down"}]},
            )
        return httpx.Response(200, json={"data": [{"status": "ok", "id": "ticket-1"}]})

    result = _run(
        handler,
        lambda adapter: adapter.send(PushNotification(title="x"), ["token-1"]),
        max_retries=1,
        retry_min_delay=0.0,
    )

    assert len(attempts) == 2
    assert result[0].accepted is True


def test_send_raises_server_error_after_exhausting_retries():
    attempts: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(request)
        return httpx.Response(500, json={"errors": [{"code": "SERVER", "message": "boom"}]})

    with pytest.raises(NotificationServerError) as exc_info:
        _run(
            handler,
            lambda adapter: adapter.send(PushNotification(title="x"), ["token-1"]),
            max_retries=1,
            retry_min_delay=0.0,
        )

    assert exc_info.value.retryable is True
    assert len(attempts) == 2


def test_send_does_not_retry_bad_request():
    attempts: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(request)
        return httpx.Response(400, json={"errors": [{"code": "BAD", "message": "bad"}]})

    with pytest.raises(NotificationBadRequestError) as exc_info:
        _run(
            handler,
            lambda adapter: adapter.send(PushNotification(title="x"), ["token-1"]),
            max_retries=3,
            retry_min_delay=0.0,
        )

    assert exc_info.value.retryable is False
    assert len(attempts) == 1


def test_send_maps_timeout_to_notification_timeout_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timeout", request=request)

    with pytest.raises(NotificationTimeoutError) as exc_info:
        _run(
            handler,
            lambda adapter: adapter.send(PushNotification(title="x"), ["token-1"]),
        )

    assert exc_info.value.retryable is True


def test_check_delivery_omits_ids_without_receipt():
    requested_ids: list[list[str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = _payload(request)
        requested_ids.append(payload["ids"])
        return httpx.Response(
            200,
            json={
                "data": {
                    "id-1": {"status": "ok"},
                    "id-3": {
                        "status": "error",
                        "message": "Device is not registered",
                        "details": {"error": "DeviceNotRegistered"},
                    },
                }
            },
        )

    receipts = _run(
        handler,
        lambda adapter: adapter.check_delivery(["id-1", "id-2", "id-3"]),
    )

    assert requested_ids == [["id-1", "id-2", "id-3"]]
    assert set(receipts) == {"id-1", "id-3"}
    assert receipts["id-1"].delivered is True
    assert receipts["id-3"].delivered is False
    assert receipts["id-3"].is_device_not_registered is True


def test_check_delivery_chunks_requests():
    request_sizes: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = _payload(request)
        request_sizes.append(len(payload["ids"]))
        return httpx.Response(200, json={"data": {}})

    ids = [f"id-{i}" for i in range(1001)]
    receipts = _run(
        handler,
        lambda adapter: adapter.check_delivery(ids),
        max_receipts_per_request=1000,
    )

    assert request_sizes == [1000, 1]
    assert receipts == {}
