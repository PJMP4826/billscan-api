from enum import Enum


class BillingFileType(str, Enum):
    """Tipos de archivo asociados a un CFDI (columna `billing_files.file_type`)."""

    XML = "XML"  # Comprobante Fiscal Digital por Internet
    PDF = "PDF"  # Representación impresa del CFDI

    @property
    def extension(self) -> str:
        """Extensión de archivo usada en la key de storage."""
        return self.value.lower()

    @property
    def mime_type(self) -> str:
        """Content-Type con el que se registra el archivo en `billing_files`."""
        return {
            "XML": "application/xml",
            "PDF": "application/pdf",
        }[self.value]
