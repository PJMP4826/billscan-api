from decimal import Decimal
from datetime import date, datetime
from typing import Any


def _coerce_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, float):
        return str(Decimal(str(value)))
    return str(value)


def parse_row_to_str(row: dict[str, Any]) -> dict[str, str | None]:
    return {key: _coerce_value(value) for key, value in row.items()}


def parse_rows_to_str(rows: list[dict[str, Any]]) -> list[dict[str, str | None]]:
    return [parse_row_to_str(row) for row in rows]