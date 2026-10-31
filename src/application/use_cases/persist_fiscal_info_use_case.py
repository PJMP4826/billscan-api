from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from src.application.dtos.billing_customer_regime_dto import BillingCustomerRegimeDto
from src.config.logger import logger
from src.domain.ports.data_encryptor import DataEncryptor
from src.domain.ports.repositories.fiscal_info_repository_port import (
    FiscalInfoRepositoryPort,
)
from src.shared.errors.infrastructure_exceptions import PostgresDBException


class PersistFiscalInfoUseCase(ABC):
    """Caso de uso base para registrar la información fiscal de un usuario.

    Concentra el paso que **siempre** es igual sin importar de dónde vengan los
    datos: encriptar los campos sensibles, insertar la fila de ``fiscal_info`` y
    dar de alta cada régimen reportado en ``regimenes``.

    Las subclases solo se encargan de *obtener* los datos (desde la request o
    desde una Constancia de Situación Fiscal) y de delegar aquí:

    - :class:`~src.application.use_cases.create_fiscal_info_use_case.CreateFiscalInfoUseCase`
      (datos ya validados en la request del usuario).
    - :class:`~src.application.use_cases.create_fiscal_info_from_csf_use_case.CreateFiscalInfoFromCsfUseCase`
      (datos leídos de un PDF/imagen de la constancia).
    """

    def __init__(
        self,
        fiscal_info_repository: FiscalInfoRepositoryPort,
        encryptor: DataEncryptor,
    ) -> None:
        self._fiscal_info_repository = fiscal_info_repository
        self._encryptor = encryptor

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> None:
        """Obtiene los datos fiscales y los persiste.

        Cada subclase define la firma concreta, porque el origen de los datos
        cambia (request del usuario vs. archivo de la constancia).
        """

    async def _persist_fiscal_info(
        self,
        *,
        user_id: str,
        rfc: str,
        razon_social: str,
        email: str,
        cp: str,
        address: str | None,
        regimens: list[BillingCustomerRegimeDto],
        use_cfdi_code_default: str,
    ) -> None:
        """Encripta los datos sensibles, inserta la info fiscal y sus regímenes.

        Se registra un renglón en ``regimenes`` por cada régimen recibido: una
        constancia puede reportar varios regímenes vigentes a la vez y todos se
        conservan para que el usuario elija después.
        """
        try:
            encrypted_rfc = self._encryptor.encrypt(rfc)
            encrypted_email = self._encryptor.encrypt(email)
            encrypted_razon_social = self._encryptor.encrypt(razon_social)
            encrypted_address = self._encryptor.encrypt(address) if address else None
            encrypted_cp = self._encryptor.encrypt(cp)

            fiscal_info_id = await self._fiscal_info_repository.insert_fiscal_info(
                user_id=user_id,
                rfc=encrypted_rfc,
                razon_social=encrypted_razon_social,
                email=encrypted_email,
                cp=encrypted_cp,
                address=encrypted_address,
                use_cfdi_code_default=use_cfdi_code_default,
            )

            for regimen in regimens:
                await self._fiscal_info_repository.add_regimen(
                    fiscal_info_id=fiscal_info_id,
                    regimen_code=regimen.code.value,
                    regimen_description=regimen.code.description,
                    fecha_alta=regimen.fecha_alta_sat or date.today(),
                )
        except PostgresDBException as e:
            logger.debug(f"Error al registrar información fiscal: {e}")
            raise
