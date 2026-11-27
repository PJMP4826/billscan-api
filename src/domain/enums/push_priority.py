from enum import Enum


class PushPriority(str, Enum):
    """Prioridad de entrega de una notificación push."""

    DEFAULT = "default"
    NORMAL = "normal"
    HIGH = "high"
