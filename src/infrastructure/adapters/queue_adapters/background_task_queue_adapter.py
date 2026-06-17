from typing import Any

from fastapi import BackgroundTasks

from src.domain.ports.queue_publisher_port import QueuePublisherPort
from src.infrastructure.registries.job_registry import JobRegistry


class BackgroundTaskQueueAdapter(QueuePublisherPort):
    """
    Implementación de QueuePublisherPort sobre fastapi.BackgroundTasks.

    LIMITACIONES QUE DEBES TENER PRESENTES (no son bugs de esta clase, son la
    naturaleza de la herramienta — por eso está detrás de un puerto y no
    hablando directo con los casos de uso):

    1. No persiste. Si el proceso muere entre el 202 y que el job corra, ese
       trabajo se pierde sin dejar rastro más allá del estado
       PENDING_EXTRACTION que quedó en la BD. No hay reintento automático ni
       reconciliación: si quieres eso, lo tienes que construir tú (un job que
       barra periódicamente registros en PENDING_EXTRACTION/PROCESSING
       atascados por más de X minutos).

    2. NO es concurrente entre sí dentro del mismo request. Starlette ejecuta
       las tareas de UNA misma instancia de BackgroundTasks secuencialmente,
       una tras otra, después de responder. Si en un solo batch subes 10
       tickets y los 10 jobs se agregan a la MISMA BackgroundTasks (la del
       request que los recibió), las 10 extracciones se procesan una por una
       en el fondo, no en paralelo. Lo que ganas es que el usuario ya no
       espera bloqueado por la respuesta HTTP — no ganas paralelismo gratis.
       Si más adelante necesitas paralelismo real, ese es justo el momento de
       cambiar este adaptador por Celery con varios workers, sin tocar nada
       más arriba.

    3. No hay manejo de reintentos si el handler lanza una excepción no
       controlada — por eso el propio handler/caso de uso debe capturar sus
       errores y dejar constancia en la BD (status FAILED), nunca dejar que
       la excepción se propague sin registro.
    """

    def __init__(self, background_tasks: BackgroundTasks) -> None:
        self._background_tasks = background_tasks

    def enqueue_job(self, job_name: str, payload: dict[str, Any]) -> None:
        handler = JobRegistry.get(job_name)
        self._background_tasks.add_task(handler, payload)
