from dataclasses import dataclass


@dataclass(frozen=True)
class FacturaGPTWebhookDelivery:
    """
    Entrada tipada de un webhook de FacturaGPT.

    La construye el controller HTTP a partir del `Request` — es el único
    punto donde se tocan tipos de FastAPI/HTTP. El caso de uso orquesta a
    partir de esto sin conocer la capa de transporte.

    - `raw_body`: bytes EXACTOS del body recibido. La firma HMAC se calcula
      sobre estos bytes, nunca sobre un JSON re-serializado.
    - `headers`: cabeceras HTTP normalizadas a minúsculas
      (`x-facturagpt-id`, `x-facturagpt-timestamp`, `x-facturagpt-signature`).
    """

    raw_body: bytes
    headers: dict[str, str]
