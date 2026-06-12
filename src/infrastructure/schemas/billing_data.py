from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

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
            "Si se require descargar una app en PlayStore o AppStore (Android o IOS) entonces is_billable=false por cuestiones tecnicas"
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
    expiration_date: Optional[date] = Field(
        None,
        description=(
            "Fecha exacta límite para facturar. "
            "Si el ticket indica una fecha explícita, devuélvela. "
            "Si el ticket indica un plazo en lenguaje natural (ej. 'Dispone de 30 días', "
            "'Solo facturable en el mes de consumo', 'Antes de fin de mes'), "
            "debes INFERIR Y CALCULAR la fecha exacta de expiración sumando esos días "
            "a la fecha de la transacción, o calculando el último día del mes corriente. "
            "Por ejemplo, si la compra es del 2025-04-15 y dice 'facturar en el mes', "
            "el resultado debe ser '2025-04-30'. "
            "Devuelve ÚNICAMENTE la fecha en formato YYYY-MM-DD. "
            "No incluyas el texto descriptivo original."
        ),
    )
    billing_metadata: Optional[dict[str, str]] = Field(
        default_factory=dict,
        description=(
            "Diccionario para métodos o instrucciones de facturación alternativas o adicionales. "
            "Úsalo si el ticket pide enviar correo, usar WhatsApp, descargar una App, "
            "o requiere datos extra (ej. número de sucursal, etc). "
            "Ejemplos: {'whatsapp': '5512345678', 'email': 'facturas@taqueria.com', "
            "'app_requerida': 'Wow+ Alsea', 'instrucciones': 'Enviar foto del ticket'}. "
            "Usa siempre claves descriptivas en snake_case."
        ),
    )
