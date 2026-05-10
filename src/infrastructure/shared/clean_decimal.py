from typing import Any
from decimal import Decimal, InvalidOperation

def clean_decimal(value: Any) -> Any:
    """Limpia strings de moneda y los convierte a Decimal de forma segura."""
    if value is None:
        return value
    if isinstance(value, str):
        # Quitamos símbolos comunes y espacios
        clean_value = value.replace('$', '').replace('€', '').replace(',', '').strip()
        if not clean_value: # Si el LLM manda un string vacío
            return Decimal('0.00')
        try:
            return Decimal(clean_value)
        except InvalidOperation:
            raise ValueError(f"No se pudo convertir el valor '{value}' a Decimal.")
    if isinstance(value, (int, float)):
        # Evitamos pérdida de precisión de coma flotante pasándolo a str primero
        return Decimal(str(value))
    return value