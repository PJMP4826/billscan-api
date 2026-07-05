from enum import Enum


class BillingStatus(str, Enum):
    NOT_ELIGIBLE = (
        "NOT_ELIGIBLE"  # El ticket no contiene datos de facturación (is_billable=False)
    )
    PENDING = "PENDING"  # Ticket elegible, esperando ser enviado a FacturaGPT
    PROCESSING = "PROCESSING"  # Ya se envió a FacturaGPT y esperamos el Webhook
    BILLED = "BILLED"  # Webhook recibido con éxito (XML y PDF listos)
    FAILED = "FAILED"  # FacturaGPT rechazó la factura (RFC inválido, ticket vencido)

    @classmethod
    def map_webhook_status_event(cls, status: str) -> "BillingStatus":
        webhook_response_status = {
            "completed": cls.BILLED,
            "failed": cls.FAILED,
        }

        return webhook_response_status.get(status.lower(), cls.PROCESSING)
