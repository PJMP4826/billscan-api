from datetime import date, time
from pydantic import BaseModel, Field
from typing import Optional

class TransactionMetadata(BaseModel):
    transaction_date: Optional[date] = Field(
        None,
        description=(
            "Fecha de la compra en formato YYYY-MM-DD. "
            "En tickets mexicanos aparece como: 'Fecha: 15/03/2025', "
            "'15-03-2025', '15/03/25', '2025-03-15'. "
            "Convierte SIEMPRE a YYYY-MM-DD. "
            "Si solo ves '15 de marzo de 2025', conviértelo a 2025-03-15."
        ),
    )
    transaction_time: Optional[time] = Field(
        None,
        description=(
            "Hora de la compra en formato 24h HH:MM. "
            "En México suele aparecer como 'Hora: 14:35', '14:35:22', "
            "o en formato 12h '02:35 PM'. Convierte SIEMPRE a 24h. "
            "Algunos tickets agrupan fecha y hora en una línea: '15/03/2025 14:35'."
        ),
    )
    ticket_number: Optional[str] = Field(
        None,
        description=(
            "Identificador único de la venta. En México aparece como: "
            "'Ticket: 12345678', 'Folio: 98765432', 'Factura: 0000123456', "
            "'Transacción: TRX-0012345', 'No. Ticket: 4567891234', "
            "'Núm. de ticket: 12345'. "
            "Suele ser un número entero largo (8-14 dígitos) ubicado cerca de la fecha. "
            "En tickets de autoservicio (Walmart, Soriana) suele ser de 10-12 dígitos. "
            "Para gasolineras Pemex/G500, es un folio de 6-8 dígitos."
        ),
    )
    pos_id: Optional[str] = Field(
        None,
        description=(
            "Número de caja/terminal. En México: 'Caja: 0012', 'Terminal: 0005', "
            "'Cajero: 015', 'T.P.V.: 003', 'POS: 0012'. "
            "Suele ser un número de 1-4 dígitos. "
            "En tickets de autoservicio está en la línea del encabezado. "
            "En OXXO y tiendas de conveniencia puede llamarse 'T.Caja' o 'CAJA'."
        ),
    )
    cashier: Optional[str] = Field(
        None,
        description=(
            "Nombre o ID del cajero. En México: 'Atendió: Juan Pérez', "
            "'Cajero: 12345', 'Vendedor: María López', 'Le atendió: Carlos'. "
            "Puede ser un nombre completo, solo nombre, o un código numérico. "
            "En gasolineras suele ser un nombre seguido de 'Despachador:'. "
            "En OXXO y similares suele ser un código de empleado de 3-5 dígitos."
        ),
    )
