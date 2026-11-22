from src.application.dtos.billing_customer_regime_dto import BillingCustomerRegimeDto
from src.application.use_cases.persist_fiscal_info_use_case import (
    PersistFiscalInfoUseCase,
)
from src.domain.value_objects.user_id import UserId


class CreateFiscalInfoUseCase(PersistFiscalInfoUseCase):
    """Registra la información fiscal que el usuario envía ya capturada.

    La parte común (encriptar + persistir) vive en
    :class:`~src.application.use_cases.persist_fiscal_info_use_case.PersistFiscalInfoUseCase`;
    aquí solo se valida el régimen que llegó en la request.
    """

    async def execute(
        self,
        user_id: UserId,
        rfc: str,
        razon_social: str,
        email: str,
        cp: str,
        address: str | None,
        regimens: list[BillingCustomerRegimeDto],
        use_cfdi_code_default: str,
    ) -> bool:
        """Crea o actualiza la información fiscal del usuario y sus regímenes."""

        return await self._persist_fiscal_info(
            user_id=user_id.value,
            rfc=rfc,
            razon_social=razon_social,
            email=email,
            cp=cp,
            address=address,
            regimens=regimens,
            use_cfdi_code_default=use_cfdi_code_default,
        )
