from typing import Any
from src.config.logger import logger
from src.domain.ports.queue_publisher_port import QueuePublisherPort

class NullQueuePublisher(QueuePublisherPort):
    """
    Adaptador de escape para cuando no hay un request HTTP activo
    Evita que el sistema truene al instanciar casos de uso en segundo plano
    """
    def enqueue_job(self, job_name: str, payload: dict[str, Any]) -> None:
        logger.info(
            f"[NullQueue] Se solicitó encolar el job '{job_name}' "
            f"con el payload: {payload}. (Ignorado o manejado síncronamente en logs)."
        )