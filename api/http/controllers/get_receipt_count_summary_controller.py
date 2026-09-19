from fastapi import status
from fastapi.responses import JSONResponse

from src.bootstraps.use_cases_bootstrap import get_receipt_count_summary_use_case


class GetReceiptCountSummaryController:
    def __init__(self) -> None:
        self._use_case = get_receipt_count_summary_use_case()

    async def handle(self) -> JSONResponse:
        try:
            result = await self._use_case.execute()

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": 200,
                    "data": result.to_dict(),
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
