from src.application.use_cases.persist_fiscal_info_use_case import (
    PersistFiscalInfoUseCase,
)
from src.domain.ports.billing_customer_info_extractor_port import (
    BillingCustomerInfoExtractorPort,
)
from src.domain.ports.data_encryptor import DataEncryptor
from src.domain.ports.repositories.fiscal_info_repository_port import (
    FiscalInfoRepositoryPort,
)
from src.domain.value_objects.user_id import UserId


class CreateFiscalInfoFromCsfUseCase(PersistFiscalInfoUseCase):
    """Registra la información fiscal leída de una Constancia de Situación Fiscal.

    El archivo (PDF, JPG o PNG) se recibe como ``bytes`` + ``mime_type`` porque
    el controller es quien lo extrae del ``UploadFile``; así el caso de uso no
    depende de FastAPI.

    El ``email`` y el ``use_cfdi_code_default`` **no** vienen en la constancia,
    por lo que se piden como parámetros de :meth:`execute`.
    """

    def __init__(
        self,
        fiscal_info_repository: FiscalInfoRepositoryPort,
        encryptor: DataEncryptor,
        extractor: BillingCustomerInfoExtractorPort,
    ) -> None:
        super().__init__(
            fiscal_info_repository=fiscal_info_repository, encryptor=encryptor
        )
        self._extractor = extractor

    async def execute(
        self,
        user_id: UserId,
        file_bytes: bytes,
        mime_type: str,
        email: str,
        use_cfdi_code_default: str,
    ) -> bool:
        """Extrae los datos de la constancia, los encripta y los persiste."""
        fiscal_identity = await self._extractor.extract(
            file_bytes=file_bytes, mime_type=mime_type
        )

        return await self._persist_fiscal_info(
            user_id=user_id.value,
            rfc=fiscal_identity.rfc,
            razon_social=fiscal_identity.razon_social,
            email=email,
            cp=fiscal_identity.cp,
            address=fiscal_identity.address,
            # La constancia puede reportar varios regímenes vigentes: se
            # registran todos y la elección queda para el usuario.
            regimens=fiscal_identity.regimens,
            use_cfdi_code_default=use_cfdi_code_default,
        )
