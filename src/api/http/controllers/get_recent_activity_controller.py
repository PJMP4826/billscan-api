from fastapi import status
from fastapi.responses import JSONResponse

from src.bootstraps.use_cases_bootstrap import get_recent_activity_use_case
from src.api.http.requests.get_recent_activity_request import (
    GetRecentActivityRequest,
)


class GetRecentActivityController:
    def __init__(self) -> None:
        self._use_case = get_recent_activity_use_case()

    async def handle(self, request_data: GetRecentActivityRequest) -> JSONResponse:
        try:
            results = await self._use_case.execute(
                receipt_uuid=request_data.receipt_uuid,
                status_filter=request_data.status_filter,
                limit=request_data.limit,
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": 200,
                    "data": [item.to_dict() for item in results],
                },
            )

        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "title": "BAD REQUEST",
                    "status": 400,
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
