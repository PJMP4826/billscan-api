from fastapi import status
from fastapi.responses import JSONResponse

from api.http.requests.get_cfdi_detail_request import GetCfdiDetailRequest
from src.bootstraps.use_cases_bootstrap import get_cfdi_detail_use_case
from src.domain.value_objects.user_id import UserId


class GetCfdiDetailController:
    def __init__(self) -> None:
        self._use_case = get_cfdi_detail_use_case()

    async def handle(
        self, user_id: UserId, request: GetCfdiDetailRequest
    ) -> JSONResponse:
        try:
            result = await self._use_case.execute(
                user_id=user_id, receipt_uuid=request.receipt_uuid
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
