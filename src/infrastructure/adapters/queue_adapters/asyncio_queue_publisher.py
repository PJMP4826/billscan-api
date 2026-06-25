import asyncio
from typing import Any
from src.config.logger import logger
from src.domain.ports.queue_publisher_port import QueuePublisherPort
from src.infrastructure.registries.job_registry import JobRegistry

class AsyncioQueuePublisher(QueuePublisherPort):
    """
    Adaptador para encolar trabajos directamente en el event loop de asyncio.
    Ideal para encadenar jobs (Worker -> Worker) cuando ya no hay un request HTTP.
    """
    def enqueue_job(self, job_name: str, payload: dict[str, Any]) -> None:
        try:
            handler = JobRegistry.get(job_name)
            # Crea una tarea en segundo plano nativa de Python sin bloquear la ejecución actual
            asyncio.create_task(handler(payload))
            logger.debug(f"[AsyncioQueue] Job '{job_name}' disparado en background.")
        except Exception as exc:
            logger.error(f"[AsyncioQueue] Error al disparar el job '{job_name}': {exc}")