import base64

from src.config.logger import logger
from src.config.settings import settings
from src.domain.enums.billing_status import BillingStatus
from src.domain.ports.billing_provider import BillingProviderPort
from src.domain.enums.tax_regime import TaxRegime
from src.domain.enums.invoice_use import InvoiceUse
from src.domain.enums.sat_payment_methods import SatPaymentMethodCode
from src.application.commands.invoice_request_command import InvoiceRequestCommand
from src.domain.ports.file_storage_port import FileStoragePort
from src.application.dtos.billing_customer_dto import BillingCustomerInfoDto
from src.domain.ports.repositories.fiscal_info_repository_port import (
    FiscalInfoRepositoryPort,
)
from src.domain.ports.repositories.receipt_billing_detail_repository_port import (
    ReceiptBillingDetailRepositoryPort,
)
from src.domain.ports.repositories.receipt_image_repository_port import (
    ReceiptImageRepositoryPort,
)
from src.domain.ports.repositories.receipt_repository_port import ReceiptRepositoryPort
from src.domain.ports.data_encryptor import DataEncryptor


class InitiateBillingUseCase:
    def __init__(
        self,
        billing_provider: BillingProviderPort,
        billing_detail_repository: ReceiptBillingDetailRepositoryPort,
        fiscal_info_repository_port: FiscalInfoRepositoryPort,
        receipt_image_repository_port: ReceiptImageRepositoryPort,
        receipt_repository: ReceiptRepositoryPort,
        encryptor: DataEncryptor,
        file_storage: FileStoragePort,
    ) -> None:
        self._billing_provider = billing_provider
        self._billing_detail_repository = billing_detail_repository
        self._fiscal_info_repository = fiscal_info_repository_port
        self._receipt_image_repository = receipt_image_repository_port
        self._receipt_repository = receipt_repository
        self._encryptor = encryptor
        self._file_storage = file_storage

    async def execute(self, payload: dict[str, str | int]) -> None:
        receipt_id = int(payload["receipt_id"])
        user_id = str(payload["user_id"])

        response = None
        try:
            # Obtener las imagenes del ticket necesarias para la factura

            # Esta es una list de images, por ahora no se uniran las imagenes (un ticket puede tener varias fotos)
            # solo se contemplara una unica imagen por ticket (image[0])
            image = await self._receipt_image_repository.find_by_receipt_id(
                receipt_id=receipt_id
            )

            image = image[0]

            img_bytes, _ = await self._file_storage.download(image["file_key"])

            image_base64 = base64.b64encode(img_bytes).decode("utf-8")

            fiscal_user_info = await self._fiscal_info_repository.get_latest_by_user_id(
                user_id=user_id
            )

            # El uso de CFDI y el régimen los elige el cliente en la request del
            # ticket y quedan persistidos en `receipt_billing_details`. Si no los
            # envió, caemos a los valores por defecto de `fiscal_info` para
            # mantener compatibilidad con clientes viejos.
            billing_detail = await self._billing_detail_repository.find_by_receipt_id(
                receipt_id=receipt_id
            )

            persisted_uso_cfdi = (
                billing_detail.get("uso_cfdi") if billing_detail else None
            )
            persisted_regimen = (
                billing_detail.get("regimen_code") if billing_detail else None
            )

            effective_uso_cfdi = (
                persisted_uso_cfdi or fiscal_user_info["use_cfdi_default"]
            )
            effective_regimen = persisted_regimen or fiscal_user_info["regimen_code"]

            await self._billing_detail_repository.set_billing_preferences(
                receipt_id=receipt_id,
                uso_cfdi=effective_uso_cfdi,
                regimen_code=effective_regimen,
            )

            user_info = BillingCustomerInfoDto(
                razon_social=self._encryptor.decrypt(fiscal_user_info["razon_social"]),
                rfc=self._encryptor.decrypt(fiscal_user_info["rfc"]),
                email=self._encryptor.decrypt(fiscal_user_info["fiscal_email"]),
                regimen=TaxRegime(effective_regimen),
                cp=self._encryptor.decrypt(fiscal_user_info["cp"]),
                address=self._encryptor.decrypt(fiscal_user_info["address"]),
            )

            receipt = await self._receipt_repository.find_by_id(receipt_id=receipt_id)

            request = InvoiceRequestCommand(
                ticket_image_b64=image_base64,
                external_id=receipt.receipt_uuid,
                payment_method=SatPaymentMethodCode(
                    (
                        receipt.payment.method_code.value
                        if receipt.payment.method_code
                        else None
                    )
                ),
                invoice_use=InvoiceUse(effective_uso_cfdi),
                customer_info=user_info,
                test_mode=settings.facturagpt_test_mode,
            )

            logger.info(f"Iniciando timbrado externo para el receipt {receipt_id}...")

            response = await self._billing_provider.submit_invoice(request=request)

            # 4. Actualizar con el Session ID externo que te da FacturaGPT
            await self._billing_detail_repository.update_billing_status(
                receipt_id=receipt_id,
                billing_status=BillingStatus.PROCESSING,
                facturagpt_session_id=response.session_id,
                billing_error_code=response.error_code,
                billing_error_message=response.error_message,
            )

            logger.info(f"Receipt {receipt_id} enviado a servicio de facturacion")
        except Exception as exc:
            logger.error(
                f"Error al iniciar facturación para el receipt {receipt_id}: {exc}"
            )

            error_code = response.error_code if response else "INTERNAL_ERROR"
            error_message = str(response.error_message) if response else str(exc)

            await self._billing_detail_repository.update_billing_status(
                receipt_id=receipt_id,
                billing_status=BillingStatus.FAILED,
                billing_error_code=error_code,
                billing_error_message=error_message,
            )
