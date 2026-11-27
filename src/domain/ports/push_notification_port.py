from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.application.dtos.push_notification_dto import (
    PushDeliveryReceipt,
    PushNotification,
    PushNotificationResult,
)


class PushNotificationPort(ABC):
    """Puerto para enviar notificaciones push a través de algún canal.

    Los fallos de una petición completa se lanzan como errores de
    infraestructura. Los fallos por destinatario se devuelven en
    ``PushNotificationResult`` para no perder el resto del lote.
    """

    @abstractmethod
    async def send(
        self, notification: PushNotification, tokens: Sequence[str]
    ) -> list[PushNotificationResult]:
        """Envía una notificación a cada token; un resultado por token."""
        raise NotImplementedError

    @abstractmethod
    async def check_delivery(
        self, delivery_ids: Sequence[str]
    ) -> dict[str, PushDeliveryReceipt]:
        """Consulta los recibos de entrega de ids obtenidos al enviar.

        Solo los ids con recibo disponible aparecen en el resultado.
        """
        raise NotImplementedError
