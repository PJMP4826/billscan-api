from fastapi import status
from fastapi.responses import JSONResponse

from api.http.requests.get_cfdi_detail_request import GetCfdiDetailRequest
from src.bootstraps.use_cases_bootstrap import get_cfdi_detail_use_case


class GetCfdiDetailController:
    def __init__(self) -> None:
        self._use_case = get_cfdi_detail_use_case()

    async def handle(self, request: GetCfdiDetailRequest) -> JSONResponse:
        try:
            temp_user_id = "ac9890c6-194b-4b7e-9aa0-2caae7db6c17"
            result = await self._use_case.execute(
                user_id=temp_user_id, receipt_uuid=request.receipt_uuid
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": 200,
                    "data": result,
                },
            )

        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "title": "NOT FOUND",
                    "status": 404,
                    "message": str(e),
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
