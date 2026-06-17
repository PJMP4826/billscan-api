from abc import ABC, abstractmethod
from typing import Any


class QueuePublisherPort(ABC):
    @abstractmethod
    def enqueue_job(self, job_name: str, payload: dict[str, Any]) -> None:
        """
        Encola un trabajo para que se procese fuera del ciclo de vida del
        request HTTP actual.

        REGLA OBLIGATORIA: 'payload' debe ser serializable a JSON y NUNCA debe
        contener bytes crudos de imágenes ni objetos de dominio complejos.
        Solo identificadores (receipt_id, claves de storage, etc.).

        Esto aplica incluso con el adaptador actual (BackgroundTasks, que
        técnicamente no te obligaría a serializar nada porque corre en el
        mismo proceso). Si no respetas esta regla desde ahora, el día que
        cambies a Celery/Redis el payload SÍ tiene que cruzar la red
        serializado, y vas a tener que reescribir los handlers, no solo el
        adaptador — que es justo lo que este puerto se supone que evita.
        """
        raise NotImplementedError
