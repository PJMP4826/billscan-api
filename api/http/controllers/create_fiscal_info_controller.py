from fastapi import status
from fastapi.responses import JSONResponse

from api.http.requests.fiscal_info_request import CreateFiscalInfoRequest
from src.bootstraps.use_cases_bootstrap import get_create_fiscal_info_use_case
from src.domain.value_objects.user_id import UserId


class CreateFiscalInfoController:
    def __init__(self) -> None:
        self._use_case = get_create_fiscal_info_use_case()

    async def handle(
        self, user_id: UserId, request_data: CreateFiscalInfoRequest
    ) -> JSONResponse:
        await self._use_case.execute(
            user_id=user_id,
            rfc=request_data.rfc,
            razon_social=request_data.razon_social,
            email=request_data.email,
            cp=request_data.cp,
            address=request_data.address,
            regimens=request_data.regimens,
            use_cfdi_code_default=request_data.use_cfdi_code_default,
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": 201,
                "message": "Información fiscal registrada exitosamente",
            },
        )
