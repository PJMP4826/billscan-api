from enum import Enum


class InvoiceQuotaStatus(str, Enum):
    """Estado de consumo en `invoice_quota_usages.status`."""

    RESERVED = "RESERVED"
    CONSUMED = "CONSUMED"
    RELEASED = "RELEASED"
