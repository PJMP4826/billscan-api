import puremagic
from fastapi import UploadFile, status
from fastapi.responses import JSONResponse

from api.http.requests.fiscal_info_from_csf_request import (
    CreateFiscalInfoFromCsfRequest,
)
from src.bootstraps.use_cases_bootstrap import (
    get_create_fiscal_info_from_csf_use_case,
)
from src.domain.value_objects.user_id import UserId
from src.shared.errors.base_exception import BadRequestError


class CreateFiscalInfoFromCsfController:
    """Registra la info fiscal leyéndola de una Constancia de Situación Fiscal."""

    ALLOWED_MIME_TYPES = ["image/jpeg", "image/jpg", "image/png", "application/pdf"]

    def __init__(self) -> None:
        self._use_case = get_create_fiscal_info_from_csf_use_case()

    async def handle(
        self,
        user_id: UserId,
        file: UploadFile,
        request_data: CreateFiscalInfoFromCsfRequest,
    ) -> JSONResponse:
        try:
            mime_type = await self._validate(file)
            content = await file.read()

            await self._use_case.execute(
                user_id=user_id,
                file_bytes=content,
                mime_type=mime_type,
                email=request_data.email,
                use_cfdi_code_default=request_data.use_cfdi_code_default.value,
            )

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "status": 201,
                    "message": "Información fiscal registrada exitosamente",
                },
            )

        except ValueError as e:
            # Captura el error lanzado cuando el TaxRegime no es válido
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "title": "BAD REQUEST",
                    "status": 400,
                    "message": str(e),
                },
            )
        except BadRequestError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "title": "BAD REQUEST",
                    "status": 400,
                    "message": e.get_message(),
                },
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "title": "Internal Server Error",
                    "status": 500,
                    "message": str(e),
                },
            )

    async def _validate(self, file: UploadFile) -> str:
        """Revisa el contenido real del archivo y devuelve su mime type."""
        head = await file.read(2048)
        await file.seek(0)

        try:
            real_mime = str(puremagic.from_string(head, mime=True))  # type: ignore

            if real_mime not in self.ALLOWED_MIME_TYPES:
                raise BadRequestError("Solo se permiten archivos PDF, JPG o PNG")

            return real_mime
        except puremagic.PureError:
            raise BadRequestError("Archivo no reconocido")
