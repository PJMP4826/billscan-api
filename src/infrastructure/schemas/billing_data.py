from pydantic import BaseModel, Field
from typing import Optional


class BillingData(BaseModel):
    is_billable: bool = Field(
        ...,
        description=(
            "True si el ticket contiene instrucciones para solicitar factura fiscal. "
            "En México las frases clave son: 'Solicite su factura en...', "
            "'Factura fácil en...', '¿Necesitas factura?', 'Facturación electrónica:', "
            "'Para facturar ingrese a...', 'Esta es una representación impresa de un CFDI', "
            "'Comprobante Fiscal Digital', 'Factura sin costo en...'. "
            "Si no hay ninguna de estas frases, is_billable=false."
        ),
    )
    has_qr_code: bool = Field(
        False,
        description=(
            "True si el ticket muestra un código QR para facturación. "
            "En México los tickets del SAT/CFDI tienen un QR grande "
            "que contiene la URL del comprobante fiscal. "
            "No confundir con códigos QR de membresías o promociones."
        ),
    )
    billing_url: Optional[str] = Field(
        None,
        description=(
            "URL del portal de facturación. En México: 'www.facturaenlinea.com.mx', "
            "'factura.pemex.com', 'www.soriana.com/facturacion', "
            "'facturacion.walmart.com.mx', 'portal.facturación.com.mx'. "
            "A veces la URL está incompleta y hay que inferir 'https://'."
        ),
    )
    billing_code: Optional[str] = Field(
        None,
        description=(
            "Código alfanumérico para facturar. En México se llama: "
            "'Clave para facturar:', 'Referencia:', 'Código de facturación:', "
            "'UUID:', 'Folio Fiscal:', o simplemente un código como "
            "'XFB ZXS MKK JJH' (4 grupos de 4 caracteres). "
            "También puede ser una cadena alfanumérica larga sin espacios."
        ),
    )
    barcode: Optional[str] = Field(
        None,
        description=(
            "Código de barras numérico para facturación. "
            "En México aparece en tickets de H&M, iShop, Mixup, "
            "y tiendas departamentales como Liverpool o Sears. "
            "Es un número muy largo (16-24 dígitos) impreso como código de barras "
            "con el número debajo (ej. '20210729003500709921'). "
            "NO es el mismo código que el SKU o UPC del producto."
        ),
    )
    expiration_date: Optional[str] = Field(
        None,
        description=(
            "Fecha o plazo límite para facturar. En México: "
            "'Dispone de 30 días para solicitarla', "
            "'Solo facturable en el mes de consumo', "
            "'Vigencia para facturar: 31/12/2025', "
            "'Facturar antes de 30 días naturales', "
            "'Fecha límite: 15/04/2025'. "
            "Captura la fecha exacta si aparece (YYYY-MM-DD) o el texto descriptivo."
        ),
    )
