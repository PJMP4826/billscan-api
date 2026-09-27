from typing import Any
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum


def json_safe(value: Any) -> Any:
    """Convierte valores no serializables por json a tipos JSON-safe."""
    if isinstance(value, Enum):
        return json_safe(value.value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}  # type: ignore
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]  # type: ignore
    return value
