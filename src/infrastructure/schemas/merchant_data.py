from pydantic import BaseModel, Field
from typing import Optional


class MerchantData(BaseModel):
    name: str = Field(
        ...,
        description=(
            "Nombre comercial o razón social visible en el ticket. "
            "Suele estar en la parte superior en letras grandes. "
            "Ej: 'Walmart de México', 'Superama', 'Soriana Híper', 'H&M', "
            "'Farmacias del Ahorro', 'OXXO', 'AutoZone', 'Chedraui', "
            "'Petróleos Mexicanos - PEMEX', 'Corporativo G500', 'Mercado Soriana', "
            "'Sanborns', 'La Comer', '7-Eleven'. "
            "Si solo aparece el logo sin nombre, infiérelo del diseño y colores. "
            "Si el nombre está abreviado (ej. 'WAL-MEX'), expándelo a su forma comercial completa."
        ),
    )
    tax_id: Optional[str] = Field(
        None,
        description=(
            "Identificador fiscal del emisor. En México es el RFC "
            "(12 caracteres para persona moral: 3 letras+6 dígitos+3 caracteres; "
            "o 13 caracteres para persona física: 4 letras+6 dígitos+3 caracteres). "
            "Suele aparecer como 'RFC:', 'R.F.C.:', 'Emisor:', 'Datos Fiscales'. "
            "En tickets de Pemex puede venir como 'PEM920508Q48'. "
            "No confundir con el RFC del cliente/usuario."
        ),
    )
    address: Optional[str] = Field(
        None,
        description=(
            "Dirección de la sucursal. En tickets mexicanos suele incluir: "
            "calle y número, colonia, código postal, ciudad, estado. "
            "Ej: 'Av. Revolución 1234, Col. Del Valle, C.P. 03100, CDMX'. "
            "Suele aparecer debajo del nombre del comercio o al pie del ticket "
            "junto con 'Sucursal:' o 'Domicilio Fiscal:'."
        ),
    )
    branch_id: Optional[str] = Field(
        None,
        description=(
            "Identificador de sucursal o tienda. En México aparece como: "
            "'Suc: 1234', 'Tienda: 5678', 'Sucursal 0890', 'Estación: 12345' (gasolineras), "
            "'Tienda Virtual', o un número precedido por 'TT' (ej. 'TT 001234'). "
            "En gasolineras Pemex/G500 suele ser un número de 4-5 dígitos "
            "junto con la dirección de la estación."
        ),
    )
    phone: Optional[str] = Field(
        None,
        description=(
            "Teléfono de la sucursal. Formato mexicano típico: '(55) 1234-5678', "
            "'01 800 123 4567' (líneas de atención), o '55 1234 5678'. "
            "Suele venir etiquetado como 'Tel:', 'Tels.:', 'Atención a clientes:'."
        ),
    )
