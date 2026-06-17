from typing import Any, Awaitable, Callable

JobHandler = Callable[[dict[str, Any]], Awaitable[None]]


class JobRegistry:
    """
    Tabla de despacho job_name -> handler.

    Por qué existe: el adaptador de cola (BackgroundTasks hoy, Celery/Redis
    después) no debe conocer los casos de uso directamente, solo conoce un
    job_name y un payload (string + dict, lo único que sobrevive serializado
    en cualquier tecnología de cola). Este registro es el único lugar que
    traduce ese job_name a la función concreta que lo ejecuta. Cambiar de
    adaptador de cola más adelante implica tocar SOLO el adaptador, nunca
    este archivo ni los casos de uso.
    """

    _handlers: dict[str, JobHandler] = {}

    @classmethod
    def register(cls, job_name: str) -> Callable[[JobHandler], JobHandler]:
        def decorator(handler: JobHandler) -> JobHandler:
            cls._handlers[job_name] = handler
            return handler

        return decorator

    @classmethod
    def get(cls, job_name: str) -> JobHandler:
        if job_name not in cls._handlers:
            raise ValueError(
                f"No hay handler registrado para el job '{job_name}'. "
                f"¿Olvidaste importar el módulo que lo registra al arrancar la app?"
            )
        return cls._handlers[job_name]
