import asyncio
import os
import tempfile
from collections.abc import Awaitable, Callable
from typing import Final

import puremagic
from csf_scraper import (
    CsfImageExtractor,
    CsfScraperException,
    ImageReaderPort,
    PersonaFisica,
    PersonaMoral,
    Regimen,
    Scraper,
)
from csf_scraper.exceptions.image_reader import (
    CifFromImageNotFoundException,
    InvalidImageException,
    InvalidImageFormatException,
    RfcFromImageNotFoundException,
)
from csf_scraper.exceptions.pdf_reader import (
    CifFromPdfNotFoundException,
    EmptyPdfContentException,
    RfcFromPdfNotFoundException,
)
from csf_scraper.exceptions.value_objects import (
    InvalidIdCifFormatException,
    InvalidRfcFormatException,
)

from src.application.dtos.csf_fiscal_identity_dto import CsfFiscalIdentityDto
from src.application.dtos.billing_customer_regime_dto import BillingCustomerRegimeDto
from src.config.logger import logger
from src.domain.enums.tax_regime import TaxRegime
from src.domain.ports.billing_customer_info_extractor_port import (
    BillingCustomerInfoExtractorPort,
)
from src.shared.errors.base_exception import BadRequestError
from src.shared.errors.infrastructure_exceptions import InfrastructureException

#: Persona que devuelve cualquier estrategia de lectura.
_Persona = PersonaMoral | PersonaFisica

#: Firma de una estrategia de lectura: (scraper, ruta) -> persona.
_CsfReader = Callable[[Scraper, str], Awaitable[_Persona]]

#: Alias MIME que mandan algunos clientes para formatos que ya soportamos.
#: ``.jpg`` y ``.jpeg`` son el mismo formato, pero el MIME no estándar
#: ``image/jpg`` es común en navegadores y móviles.
_MIME_ALIASES: Final[dict[str, str]] = {
    "image/jpg": "image/jpeg",
    "image/pjpeg": "image/jpeg",
    "image/jfif": "image/jpeg",
    "image/x-png": "image/png",
}

#: Fallos que significan "el archivo no sirve" (entrada inválida del cliente).
_INVALID_INPUT_EXCEPTIONS: Final[tuple[type[Exception], ...]] = (
    InvalidImageException,
    InvalidImageFormatException,
    InvalidRfcFormatException,
    InvalidIdCifFormatException,
    CifFromImageNotFoundException,
    CifFromPdfNotFoundException,
    RfcFromImageNotFoundException,
    RfcFromPdfNotFoundException,
    EmptyPdfContentException,
)


class BillingCustomerInfoExtractor(BillingCustomerInfoExtractorPort):
    def __init__(self, image_reader: ImageReaderPort) -> None:
        # ``Scraper`` consume un ``RfcCifExtractorPort``: se adapta el motor de
        # lectura (``ImageReaderPort``) con ``CsfImageExtractor``.
        self._image_extractor = CsfImageExtractor(image_reader)

        # Estrategias de lectura: MIME type -> (sufijo del temporal, lector).
        # Agregar un formato soportado es agregar una entrada aquí.
        self._readers: dict[str, tuple[str, _CsfReader]] = {
            "application/pdf": ("pdf", self._read_pdf),
            "image/jpeg": ("jpg", self._read_image),
            "image/png": ("png", self._read_image),
        }

    async def _read_pdf(self, scraper: Scraper, file_path: str) -> _Persona:
        return await scraper.obtain_from_pdf_path(path=file_path)

    async def _read_image(self, scraper: Scraper, file_path: str) -> _Persona:
        return await scraper.obtain_from_image_path(path=file_path)

    async def extract(self, file_bytes: bytes, mime_type: str) -> CsfFiscalIdentityDto:
        suffix, read = self._readers[self._detect_kind(file_bytes, mime_type)]

        file_path = await asyncio.to_thread(
            self._write_temp_file, file_bytes, f".{suffix}"
        )

        try:
            async with Scraper.create(image_extractor=self._image_extractor) as scraper:
                person = await read(scraper, file_path)
        except _INVALID_INPUT_EXCEPTIONS as exception:
            raise BadRequestError(
                "No se pudieron leer los datos fiscales del archivo. "
                "Verifica que sea una Constancia de Situación Fiscal vigente.",
                error_code="INVALID_CSF_FILE",
                details={"reason": str(exception)},
            ) from exception
        except CsfScraperException as exception:
            raise InfrastructureException(
                "No fue posible consultar los datos fiscales en el SAT.",
                error_code="CSF_LOOKUP_FAILED",
                details={"reason": str(exception)},
            ) from exception
        except FileNotFoundError as exception:
            # ``CsfPdfExtractor`` depende del binario ``pdftotext``
            # (paquete ``poppler-utils``); sin él el PDF no se puede leer.
            raise InfrastructureException(
                "Falta la dependencia del sistema para leer PDFs (pdftotext).",
                error_code="CSF_PDF_TOOL_MISSING",
                details={"reason": str(exception)},
            ) from exception
        finally:
            await asyncio.to_thread(self._remove_temp_file, file_path)

        return self._to_dto(person)

    def _to_dto(self, person: PersonaMoral | PersonaFisica) -> CsfFiscalIdentityDto:
        if person.rfc is None:
            raise BadRequestError(
                "La constancia no contiene un RFC válido.",
                error_code="CSF_RFC_MISSING",
            )

        if isinstance(person, PersonaMoral):
            razon_social = person.razon_social
        else:
            razon_social = self._full_name(person)

        return CsfFiscalIdentityDto(
            razon_social=razon_social,
            rfc=person.rfc.value,
            cp=person.codigo_postal,
            regimens=self._map_regimens(person.regimenes),
            address=self._build_address(person),
        )

    def _detect_kind(self, file_bytes: bytes, mime_type: str) -> str:
        """Determina el tipo real del archivo (magic bytes primero).

        El ``mime_type`` que manda el cliente es solo una pista: puede venir con
        parámetros (``application/pdf; boundary=...``), ser genérico o usar un
        alias no estándar (``image/jpg``).
        """
        try:
            guessed = str(puremagic.from_string(file_bytes, mime=True))  # type: ignore
        except puremagic.PureError:
            guessed = None

        if guessed in self._readers:
            return guessed

        hinted = self._normalize_mime(mime_type)
        if hinted in self._readers:
            return hinted

        raise BadRequestError(
            "Formato no soportado: se espera un PDF, JPG o PNG de la "
            "Constancia de Situación Fiscal.",
            error_code="UNSUPPORTED_CSF_FORMAT",
            details={"mime_type": mime_type, "detected": guessed},
        )

    @staticmethod
    def _normalize_mime(mime_type: str) -> str:
        """Descarta parámetros y resuelve alias (``image/jpg`` -> ``image/jpeg``)."""
        normalized = (mime_type or "").split(";", 1)[0].strip().lower()
        return _MIME_ALIASES.get(normalized, normalized)

    def _write_temp_file(self, file_bytes: bytes, suffix: str) -> str:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            temp_file.write(file_bytes)
        finally:
            temp_file.close()
        return temp_file.name

    def _remove_temp_file(self, file_path: str) -> None:
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass

    def _map_regimens(self, regimens: list[Regimen]) -> list[BillingCustomerRegimeDto]:
        """Mapea los regímenes de la constancia **sin elegir uno**.

        Se conserva el orden en que los reporta el SAT y ``fecha_alta_sat``
        queda como dato informativo: varios regímenes pueden estar vigentes a
        la vez, así que no sirve para decidir cuál aplica.
        """
        if not regimens:
            raise BadRequestError(
                "La constancia no reporta regímenes fiscales.",
                error_code="CSF_NO_REGIMEN",
            )

        candidates: list[BillingCustomerRegimeDto] = []

        for regimen in regimens:
            code = self._resolve_tax_regime(regimen)
            if code is None:
                # Un régimen exótico no debe impedir leer el resto de la CSF.
                logger.warning(
                    "Régimen fiscal no soportado en la constancia: %r (id=%r)",
                    regimen.regimen,
                    regimen.regimen_id,
                )
                continue
            candidates.append(
                BillingCustomerRegimeDto(code=code, fecha_alta_sat=regimen.fecha_alta)
            )

        if not candidates:
            raise BadRequestError(
                "Ninguno de los regímenes de la constancia está soportado.",
                error_code="CSF_UNSUPPORTED_REGIMEN",
                details={"regimenes": [r.regimen for r in regimens]},
            )

        return candidates

    @staticmethod
    def _resolve_tax_regime(regimen: Regimen) -> TaxRegime | None:
        """Mapea un régimen de la librería a :class:`TaxRegime`.

        El catálogo de ``csf_scraper`` no cubre todos los códigos (le faltan,
        por ejemplo, 609, 628, 629 y 630), así que si el ``regimen_id`` viene
        vacío se intenta emparejar por la descripción.
        """
        if regimen.regimen_id:
            try:
                return TaxRegime(regimen.regimen_id)
            except ValueError:
                return None

        raw = regimen.regimen.strip().upper()
        if not raw:
            return None

        for candidate in TaxRegime:
            description = candidate.description.upper()
            if description in raw or raw in description:
                return candidate

        return None

    def _full_name(self, person: PersonaFisica) -> str:
        parts = (
            person.nombre,
            person.apellido_paterno,
            person.apellido_materno,
        )
        return " ".join(part.strip() for part in parts if part and part.strip())

    def _build_address(self, data: PersonaFisica | PersonaMoral) -> str:
        # 1. Vialidad (Tipo + Nombre)
        vialidad = f"{data.tipo_vialidad or ''} {data.nombre_vialidad or ''}".strip()

        # 2. Números
        num_ext = f"NO. {data.numero_exterior}" if data.numero_exterior else ""
        num_int = f"INT. {data.numero_interior}" if data.numero_interior else ""

        # 3. Colonia
        colonia = f"COL. {data.colonia}" if data.colonia else ""

        # 4. Municipio
        municipio = data.municipio_delegacion or ""

        # 5. Código Postal
        cp = f"C.P. {data.codigo_postal}" if data.codigo_postal else ""

        # 6. Entidad Federativa
        estado = data.entidad_federativa or ""

        # Componentes ordenados
        components = [
            vialidad,
            num_ext,
            num_int,
            colonia,
            municipio,
            cp,
            estado,
        ]

        # Une únicamente los elementos que no están vacíos
        return ", ".join(part for part in components if part)
