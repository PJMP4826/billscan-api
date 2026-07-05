from enum import Enum

class BillingWebHookEventType(str, Enum):
    COMPLETED = "factura.completed"
    FAILED = "factura.failed"
    BATCH_COMPLETE = "batch.completed"