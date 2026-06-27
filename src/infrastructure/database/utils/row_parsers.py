import json
from decimal import Decimal
from datetime import date, datetime
from typing import Any, cast


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
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def _parse_json_field(value: Any) -> Any:
    """
    Ensures a field that should be JSON is returned as a native
    Python dict or list, regardless of whether Postgres returned
    it already parsed or as a raw JSON string.
    """
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return cast(dict[str, Any] | list[Any], value)
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return value
    return value


def parse_row_to_str(
    row: dict[str, Any],
    json_fields: set[str] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in row.items():
        if json_fields and key in json_fields:
            result[key] = _parse_json_field(value)
        else:
            result[key] = _coerce_value(value)
    return result


def parse_rows_to_str(
    rows: list[dict[str, Any]],
    json_fields: set[str] | None = None,
) -> list[dict[str, Any]]:
    return [parse_row_to_str(row, json_fields=json_fields) for row in rows]