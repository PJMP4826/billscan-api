from pydantic import BaseModel, Field
from typing import Optional


class TransactionMetadata(BaseModel):
    date: Optional[str] = Field(None, description="Fecha de la compra en formato YYYY-MM-DD.")
    time: Optional[str] = Field(None, description="Hora de la compra en formato HH:MM.")
    receipt_id: Optional[str] = Field(None, description="Folio, número de ticket o identificador único de la venta.")
    pos_id: Optional[str] = Field(None, description="Número de caja o terminal.")
    cashier: Optional[str] = Field(None, description="Nombre o ID del cajero/vendedor que atendió.")
