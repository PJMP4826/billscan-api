from dataclasses import dataclass
from typing import Any

from src.domain.enums.push_priority import PushPriority


@dataclass(frozen=True)
class PushNotification:
    """Contenido de una notificación push, independiente del proveedor."""

    title: str | None = None
    body: str | None = None
    data: dict[str, Any] | None = None
    sound: str | dict[str, Any] | None = None
    badge: int | None = None
    ttl: int | None = None
    expiration: int | None = None
    priority: PushPriority | None = None
    channel_id: str | None = None
    category_id: str | None = None
    icon: str | None = None


@dataclass(frozen=True)
class PushNotificationResult:
    """Resultado del envío para un destinatario.

    ``accepted`` significa que el proveedor recibió el mensaje, no que el
    dispositivo lo haya mostrado. Los fallos por destinatario se devuelven
    aquí, nunca se lanzan.
    """

    token: str
    accepted: bool
    raw: dict[str, Any]
    delivery_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    details: dict[str, Any] | None = None

    @property
    def is_ok(self) -> bool:
        return self.accepted

    @property
    def is_device_not_registered(self) -> bool:
        return self.error_code == "DeviceNotRegistered"

    @property
    def is_retryable(self) -> bool:
        return self.error_code == "MessageRateExceeded"


@dataclass(frozen=True)
class PushDeliveryReceipt:
    """Resultado de la segunda fase: ¿FCM/APNs aceptó la entrega?

    Los ids sin recibo todavía se omiten del resultado; no son un error.
    """

    delivery_id: str
    delivered: bool
    raw: dict[str, Any]
    error_code: str | None = None
    error_message: str | None = None
    details: dict[str, Any] | None = None

    @property
    def is_ok(self) -> bool:
        return self.delivered

    @property
    def is_device_not_registered(self) -> bool:
        return self.error_code == "DeviceNotRegistered"

    @property
    def is_retryable(self) -> bool:
        return self.error_code == "MessageRateExceeded"
