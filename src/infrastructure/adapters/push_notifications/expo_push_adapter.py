"""
Expo Push Notification adapter.

Implementa `PushNotificationPort` contra la API de Expo. Es el único
archivo que conoce las URLs de Expo, su formato camelCase, el flujo de
tickets/recibos, sus códigos de error y sus límites.

Fallos de una petición completa -> excepciones de
`src.shared.errors.notification_exceptions`. Fallos por destinatario ->
`PushNotificationResult` con `error_code`, sin lanzar.
"""

import asyncio
import gzip
import json
import random
from collections.abc import Sequence
from typing import Any

import httpx

from src.application.dtos.push_notification_dto import (
    PushDeliveryReceipt,
    PushNotification,
    PushNotificationResult,
)
from src.config.logger import logger
from src.domain.ports.push_notification_port import PushNotificationPort
from src.shared.errors.notification_exceptions import (
    NotificationAuthError,
    NotificationBadRequestError,
    NotificationProviderError,
    NotificationRateLimitError,
    NotificationServerError,
    NotificationTimeoutError,
    NotificationTransportError,
    NotificationUnexpectedResponseError,
)


class ExpoPushNotificationAdapter(PushNotificationPort):
    """`PushNotificationPort` implementado contra la Expo Push API."""

    BASE_URL = "https://exp.host"
    SEND_PATH = "/--/api/v2/push/send"
    RECEIPTS_PATH = "/--/api/v2/push/getReceipts"

    MAX_MESSAGES_PER_REQUEST = 100
    MAX_RECEIPTS_PER_REQUEST = 1000
    MAX_CONCURRENT_REQUESTS = 6
    GZIP_THRESHOLD_BYTES = 1024

    def __init__(
        self,
        base_url: str = BASE_URL,
        access_token: str = "",
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
        retry_min_delay: float = 1.0,
        max_messages_per_request: int = MAX_MESSAGES_PER_REQUEST,
        max_receipts_per_request: int = MAX_RECEIPTS_PER_REQUEST,
        max_concurrent_requests: int = MAX_CONCURRENT_REQUESTS,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if max_concurrent_requests < 1:
            raise ValueError("max_concurrent_requests debe ser >= 1")
        if max_retries < 0:
            raise ValueError("max_retries debe ser >= 0")

        self._base_url = base_url.rstrip("/") if base_url else self.BASE_URL
        self._access_token = access_token
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._retry_min_delay = retry_min_delay
        self._max_messages_per_request = max_messages_per_request
        self._max_receipts_per_request = max_receipts_per_request
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._client = client
        self._owns_client = client is None

    async def startup(self) -> None:
        """Crea el cliente HTTP si el adapter es dueño de su ciclo de vida."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
            self._owns_client = True
            logger.info("ExpoPushNotificationAdapter: httpx.AsyncClient inicializado.")

    async def shutdown(self) -> None:
        """Cierra el cliente HTTP si fue creado por el adapter."""
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None
            logger.info("ExpoPushNotificationAdapter: httpx.AsyncClient cerrado.")

    async def send(
        self, notification: PushNotification, tokens: Sequence[str]
    ) -> list[PushNotificationResult]:
        tokens = list(tokens)
        if not tokens:
            return []
        bad_tokens = [token for token in tokens if not token.strip()]
        if bad_tokens:
            raise NotificationBadRequestError(
                "Se recibió un token de notificación vacío o inválido",
                details={"invalid_tokens": bad_tokens},
            )

        pairs = [(notification, token) for token in tokens]
        chunks = [
            pairs[i : i + self._max_messages_per_request]
            for i in range(0, len(pairs), self._max_messages_per_request)
        ]
        per_chunk = await asyncio.gather(
            *(self._send_chunk(chunk) for chunk in chunks)
        )
        return [result for chunk in per_chunk for result in chunk]

    async def check_delivery(
        self, delivery_ids: Sequence[str]
    ) -> dict[str, PushDeliveryReceipt]:
        ids = list(delivery_ids)
        if not ids:
            return {}
        chunks = [
            ids[i : i + self._max_receipts_per_request]
            for i in range(0, len(ids), self._max_receipts_per_request)
        ]
        per_chunk = await asyncio.gather(
            *(self._get_receipts_chunk(chunk) for chunk in chunks)
        )
        receipts: dict[str, PushDeliveryReceipt] = {}
        for chunk in per_chunk:
            receipts.update(chunk)
        return receipts

    async def _send_chunk(
        self, chunk: list[tuple[PushNotification, str]]
    ) -> list[PushNotificationResult]:
        payloads = [
            self._to_expo_payload(notification, token)
            for notification, token in chunk
        ]
        envelope = await self._request_json(self._send_url, payloads)
        data = envelope.get("data")
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list) or len(data) != len(chunk):
            raise NotificationUnexpectedResponseError(
                "Expo devolvió una cantidad de tickets distinta a los mensajes enviados",
                details={
                    "expected": len(chunk),
                    "received": len(data) if isinstance(data, list) else None,
                    "envelope": envelope,
                },
            )
        return [
            self._ticket_to_result(token, raw)
            for (_, token), raw in zip(chunk, data, strict=True)
        ]

    async def _get_receipts_chunk(
        self, chunk: list[str]
    ) -> dict[str, PushDeliveryReceipt]:
        envelope = await self._request_json(
            self._receipts_url, {"ids": chunk}
        )
        data = envelope.get("data")
        if not isinstance(data, dict):
            raise NotificationUnexpectedResponseError(
                "Expo no devolvió un objeto 'data' con los recibos solicitados",
                details={"envelope": envelope},
            )
        return {
            receipt_id: self._receipt_to_delivery(receipt_id, raw)
            for receipt_id, raw in data.items()
            if isinstance(raw, dict)
        }

    async def _request_json(self, url: str, payload: Any) -> dict[str, Any]:
        client = self._ensure_client()
        body = json.dumps(payload).encode("utf-8")
        headers = self._headers()
        if len(body) > self.GZIP_THRESHOLD_BYTES:
            body = gzip.compress(body)
            headers["Content-Encoding"] = "gzip"

        last_error: NotificationProviderError | None = None
        for attempt in range(self._max_retries + 1):
            try:
                async with self._semaphore:
                    response = await client.post(
                        url, content=body, headers=headers
                    )
            except httpx.TimeoutException as exc:
                raise NotificationTimeoutError() from exc
            except httpx.RequestError as exc:
                raise NotificationTransportError(
                    f"No fue posible conectar con Expo: {exc}"
                ) from exc

            envelope = self._parse_envelope(response)
            if (
                response.status_code == 200
                and envelope is not None
                and "errors" not in envelope
            ):
                return envelope
            if response.status_code == 200 and envelope is None:
                raise NotificationUnexpectedResponseError(
                    "Expo respondió 200 con un cuerpo que no es JSON",
                    details={"response_body": response.text[:500]},
                )

            error = self._error_from_envelope(response, envelope)
            if response.status_code == 200:
                raise error
            if not error.retryable or attempt == self._max_retries:
                raise error

            last_error = error
            delay = self._retry_delay(attempt, response)
            logger.warning(
                "ExpoPushNotificationAdapter: reintento %s/%s en %.2fs (%s)",
                attempt + 1,
                self._max_retries,
                delay,
                error.error_code,
            )
            await asyncio.sleep(delay)

        raise last_error or NotificationServerError(
            "El servicio de notificaciones de Expo falló"
        )

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
            self._owns_client = True
            logger.info("ExpoPushNotificationAdapter: httpx.AsyncClient inicializado.")
        return self._client

    def _retry_delay(self, attempt: int, response: httpx.Response) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                return max(float(retry_after), 0.0)
            except ValueError:
                pass
        backoff = self._retry_min_delay * (2**attempt)
        return backoff + random.uniform(0, 0.5)

    @staticmethod
    def _parse_envelope(response: httpx.Response) -> dict[str, Any] | None:
        try:
            data = response.json()
        except ValueError:
            return None
        return data if isinstance(data, dict) else None

    def _error_from_envelope(
        self, response: httpx.Response, envelope: dict[str, Any] | None
    ) -> NotificationProviderError:
        status = response.status_code
        errors = (envelope or {}).get("errors") or []
        first = errors[0] if isinstance(errors, list) and errors else {}
        code = first.get("code") if isinstance(first, dict) else None
        message = (
            first.get("message")
            if isinstance(first, dict) and first.get("message")
            else f"El servicio de notificaciones de Expo respondió HTTP {status}"
        )
        details = {"envelope": envelope} if envelope is not None else None
        response_body = response.text[:500]

        if status == 401 or code == "UNAUTHORIZED":
            return NotificationAuthError(
                message,
                error_code=code,
                details=details,
                upstream_status_code=status,
                response_body=response_body,
            )
        if status == 429 or code == "TOO_MANY_REQUESTS":
            retry_after = response.headers.get("Retry-After")
            return NotificationRateLimitError(
                message,
                error_code=code or "TOO_MANY_REQUESTS",
                details=details,
                upstream_status_code=status,
                response_body=response_body,
                retry_after=self._parse_retry_after(retry_after),
            )
        if status >= 500:
            return NotificationServerError(
                message,
                error_code=code,
                details=details,
                upstream_status_code=status,
                response_body=response_body,
            )
        return NotificationBadRequestError(
            message,
            error_code=code,
            details=details,
            upstream_status_code=status,
            response_body=response_body,
        )

    @staticmethod
    def _parse_retry_after(value: str | None) -> float | None:
        if value is None:
            return None
        try:
            return max(float(value), 0.0)
        except ValueError:
            return None

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/json",
            "User-Agent": "billscan-api/expo-push-adapter",
        }
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    @staticmethod
    def _to_expo_payload(
        notification: PushNotification, token: str
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"to": token}
        if notification.title is not None:
            payload["title"] = notification.title
        if notification.body is not None:
            payload["body"] = notification.body
        if notification.data is not None:
            payload["data"] = notification.data
        if notification.sound is not None:
            payload["sound"] = notification.sound
        if notification.badge is not None:
            payload["badge"] = notification.badge
        if notification.ttl is not None:
            payload["ttl"] = notification.ttl
        if notification.expiration is not None:
            payload["expiration"] = notification.expiration
        if notification.priority is not None:
            payload["priority"] = notification.priority.value
        if notification.channel_id is not None:
            payload["channelId"] = notification.channel_id
        if notification.category_id is not None:
            payload["categoryId"] = notification.category_id
        if notification.icon is not None:
            payload["icon"] = notification.icon
        return payload

    @staticmethod
    def _ticket_to_result(
        token: str, raw: Any
    ) -> PushNotificationResult:
        raw = raw if isinstance(raw, dict) else {}
        details = raw.get("details") if isinstance(raw.get("details"), dict) else None
        error_code = details.get("error") if details else None
        return PushNotificationResult(
            token=token,
            accepted=raw.get("status") == "ok",
            delivery_id=raw.get("id"),
            error_code=error_code,
            error_message=raw.get("message"),
            details=details,
            raw=raw,
        )

    @staticmethod
    def _receipt_to_delivery(
        receipt_id: str, raw: dict[str, Any]
    ) -> PushDeliveryReceipt:
        details = raw.get("details") if isinstance(raw.get("details"), dict) else None
        error_code = details.get("error") if details else None
        return PushDeliveryReceipt(
            delivery_id=receipt_id,
            delivered=raw.get("status") == "ok",
            error_code=error_code,
            error_message=raw.get("message"),
            details=details,
            raw=raw,
        )

    @property
    def _send_url(self) -> str:
        return f"{self._base_url}{self.SEND_PATH}"

    @property
    def _receipts_url(self) -> str:
        return f"{self._base_url}{self.RECEIPTS_PATH}"
