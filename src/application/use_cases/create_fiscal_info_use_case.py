from datetime import datetime

from src.application.dtos.billing_customer_regime_dto import BillingCustomerRegimeDto
from src.application.use_cases.persist_fiscal_info_use_case import (
    PersistFiscalInfoUseCase,
)


class CreateFiscalInfoUseCase(PersistFiscalInfoUseCase):
    """Registra la información fiscal que el usuario envía ya capturada.

    La parte común (encriptar + persistir) vive en
    :class:`~src.application.use_cases.persist_fiscal_info_use_case.PersistFiscalInfoUseCase`;
    aquí solo se valida el régimen que llegó en la request.
    """

    async def execute(
        self,
        user_id: str,
        rfc: str,
        razon_social: str,
        email: str,
        cp: str,
        address: str | None,
        regimen_code: str,
        fecha_alta_sat: datetime,
        use_cfdi_code_default: str,
    ) -> None:
        """Crea la información fiscal de un usuario y agrega un régimen."""
        regimen = self._resolve_regimen(regimen_code)

        await self._persist_fiscal_info(
            user_id=user_id,
            rfc=rfc,
            razon_social=razon_social,
            email=email,
            cp=cp,
            address=address,
            regimens=[
                BillingCustomerRegimeDto(code=regimen, fecha_alta_sat=fecha_alta_sat)
            ],
            use_cfdi_code_default=use_cfdi_code_default,
        )
