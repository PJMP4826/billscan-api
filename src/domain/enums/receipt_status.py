from enum import Enum


class ReceiptStatus(str, Enum):
    RECEIVED = "RECEIVED"  # La imagen se subio, esperando entrar a la cola
    EXTRACTING = "EXTRACTING"  # Gemini está procesando la imagen
    COMPLETED = "COMPLETED"  # Datos extraídos y guardados con éxito
    FAILED = "FAILED"  # Gemini no pudo leer la imagen (borrosa, no es un ticket, etc.)
