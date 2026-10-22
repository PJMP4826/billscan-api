from abc import ABC, abstractmethod

from src.application.dtos.csf_fiscal_identity_dto import CsfFiscalIdentityDto


class BillingCustomerInfoExtractorPort(ABC):
    """Extrae los datos fiscales de una Constancia de Situación Fiscal.

    Devuelve :class:`CsfFiscalIdentityDto` (no el DTO de facturación) porque la
    constancia puede reportar varios regímenes vigentes y la elección del que
    se enviará al proveedor es una decisión posterior.
    """

    @abstractmethod
    async def extract(self, file_bytes: bytes, mime_type: str) -> CsfFiscalIdentityDto:
        pass
