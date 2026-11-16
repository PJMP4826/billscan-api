from fastapi import status
from fastapi.responses import JSONResponse

from src.bootstraps.use_cases_bootstrap import get_completed_billing_summary_use_case
from src.domain.value_objects.user_id import UserId


class GetCompletedBillingSummaryController:
    def __init__(self) -> None:
        self._use_case = get_completed_billing_summary_use_case()

    async def handle(self, user_id: UserId, period: str = "month") -> JSONResponse:
        result = await self._use_case.execute(user_id, period)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": 200,
                "data": result.to_dict()
            },
        )
