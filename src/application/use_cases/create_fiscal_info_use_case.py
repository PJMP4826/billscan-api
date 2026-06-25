from datetime import date

from src.config.logger import logger
from src.domain.ports.repositories.fiscal_info_repository_port import (
    FiscalInfoRepositoryPort,
)
from src.domain.enums.tax_regime import TaxRegime
from src.shared.errors.infrastructure_exceptions import PostgresDBException
from src.domain.ports.data_encryptor import DataEncryptor


class CreateFiscalInfoUseCase:
    def __init__(
        self, fiscal_info_repository: FiscalInfoRepositoryPort, encryptor: DataEncryptor
    ) -> None:
        self._fiscal_info_repository = fiscal_info_repository
        self._encryptor = encryptor

    async def execute(
        self,
        user_id: str,
        rfc: str,
        razon_social: str,
        email: str,
        cp: str,
        address: str | None,
        regimen_code: str,
        use_cfdi_code_default: str
    ) -> None:
        """Crea la información fiscal de un usuario y agrega un régimen."""
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
                use_cfdi_code_default=use_cfdi_code_default
            )

            valid_regimen = TaxRegime(regimen_code)

            await self._fiscal_info_repository.add_regimen(
                fiscal_info_id=fiscal_info_id,
                regimen_code=valid_regimen.value,
                regimen_description=valid_regimen.description,
                fecha_alta=date.today(),
            )
        except ValueError as e:
            logger.debug(f"Régimen fiscal {regimen_code} no válido: {e}")
            raise ValueError(f"Régimen fiscal {regimen_code} no válido") from e
        except PostgresDBException as e:
            logger.debug(f"Error al registrar información fiscal: {e}")
            raise
