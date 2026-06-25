from enum import Enum


class InvoiceUse(str, Enum):
    # Gastos y Mercancías
    G01 = "G01"
    G02 = "G02"
    G03 = "G03"

    # Inversiones
    I01 = "I01"
    I02 = "I02"
    I03 = "I03"
    I04 = "I04"
    I05 = "I05"
    I06 = "I06"
    I07 = "I07"
    I08 = "I08"

    # Deducciones Personales
    D01 = "D01"
    D02 = "D02"
    D03 = "D03"
    D04 = "D04"
    D05 = "D05"
    D06 = "D06"
    D07 = "D07"
    D08 = "D08"
    D09 = "D09"
    D10 = "D10"

    # Otros / Especiales
    P01 = "P01"
    S01 = "S01"
    CP01 = "CP01"
    CN01 = "CN01"

    @property
    def description(self) -> str:
        """Retorna la descripción oficial del SAT para el código de uso de CFDI."""
        _descriptions = {
            # Gastos y Mercancías
            "G01": "Adquisición de mercancías",
            "G02": "Devoluciones, descuentos o bonificaciones",
            "G03": "Gastos en general",
            # Inversiones
            "I01": "Construcciones",
            "I02": "Mobiliario y equipo de oficina por inversiones",
            "I03": "Equipo de transporte",
            "I04": "Equipo de cómputo y accesorios",
            "I05": "Dados, troqueles, moldes, matrices y herramental",
            "I06": "Comunicaciones telefónicas",
            "I07": "Comunicaciones satelitales",
            "I08": "Otra maquinaria y equipo",
            # Deducciones Personales
            "D01": "Honorarios médicos, dentales y gastos hospitalarios",
            "D02": "Gastos médicos por incapacidad o discapacidad",
            "D03": "Gastos funerales",
            "D04": "Donativos",
            "D05": "Intereses reales efectivamente pagados por créditos hipotecarios",
            "D06": "Aportaciones voluntarias al SAR",
            "D07": "Primas por seguros de gastos médicos",
            "D08": "Gastos de transportación escolar obligatoria",
            "D09": "Depósitos en cuentas para el ahorro / planes de pensiones",
            "D10": "Pagos por servicios educativos (colegiaturas)",
            # Otros / Especiales
            "P01": "Por definir",
            "S01": "Sin efectos fiscales",
            "CP01": "Pagos",
            "CN01": "Nómina",
        }
        return _descriptions.get(self.value, "Descripción no encontrada")
