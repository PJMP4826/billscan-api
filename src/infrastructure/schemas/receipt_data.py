from pydantic import BaseModel, Field
from typing import List, Optional

from src.infrastructure.schemas.merchant_data import MerchantData
from src.infrastructure.schemas.transaction_metadata import TransactionMetadata
from src.infrastructure.schemas.line_item import LineItem
from src.infrastructure.schemas.totals_and_taxes import TotalsAndTaxes
from src.infrastructure.schemas.payment_info import PaymentInfo
from src.infrastructure.schemas.billing_data import BillingData


class ReceiptData(BaseModel):
    merchant: MerchantData
    transaction: TransactionMetadata
    items: List[LineItem]
    totals: TotalsAndTaxes
    payment: PaymentInfo
    billing: Optional[BillingData] = None
    context_notes: Optional[str] = Field(
        None,
        description=(
            "Notas adicionales visibles en el ticket. "
            "En México es común ver: 'No se aceptan devoluciones', "
            "'Gracias por su compra', 'Vuelva pronto', "
            "'Horario de atención: L-V 9:00-18:00', "
            "'Conserve su ticket para cualquier aclaración', "
            "'Política de devolución: 7 días'. "
            "Si el ticket tiene texto promocional o legal al pie, resúmelo aquí."
        ),
    )
    extra_metadata: Optional[dict[str, str]] = Field(
        default_factory=dict,
        description=(
            "Diccionario clave-valor para capturar cualquier información valiosa o "
            "única del ticket que no encaje en los campos estándar. Ejemplos en México: "
            "{'puntos_lealtad_obtenidos': 15, 'saldo_monedero': 150.50, 'wifi_password': 'cafe', "
            "'codigo_encuesta_satisfaccion': '1234-5678', 'cliente_frecuente_id': '9876543'}. "
            "Usa siempre claves descriptivas en formato snake_case y valores simples."
        ),
    )
