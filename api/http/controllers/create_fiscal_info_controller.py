from fastapi import status
from fastapi.responses import JSONResponse

from api.http.requests.fiscal_info_request import CreateFiscalInfoRequest
from src.bootstraps.use_cases_bootstrap import get_create_fiscal_info_use_case
from src.shared.errors.base_exception import BadRequestError


class CreateFiscalInfoController:
    def __init__(self) -> None:
        self._use_case = get_create_fiscal_info_use_case()

    async def handle(self, request_data: CreateFiscalInfoRequest) -> JSONResponse:
        try:

            temp_user_id = "ac9890c6-194b-4b7e-9aa0-2caae7db6c17"

            await self._use_case.execute(
                user_id=temp_user_id,
                rfc=request_data.rfc,
                razon_social=request_data.razon_social,
                email=request_data.email,
                cp=request_data.cp,
                address=request_data.address,
                regimens=request_data.regimens,
                use_cfdi_code_default=request_data.use_cfdi_code_default
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
                    "message": str(e),
                },
            )
        except Exception as e:
            # Captura fallos de base de datos (PostgresDBException) u otros errores no controlados
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "title": "Internal Server Error",
                    "status": 500,
                    "message": str(e),
                },
            )
