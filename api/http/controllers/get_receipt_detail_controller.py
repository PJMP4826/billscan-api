from fastapi import status
from fastapi.responses import JSONResponse

from api.http.requests.get_receipt_detail_request import GetReceiptDetailRequest
from src.bootstraps.use_cases_bootstrap import get_receipt_detail_use_case
from src.domain.value_objects.user_id import UserId


class GetReceiptDetailController:
    def __init__(self) -> None:
        self._use_case = get_receipt_detail_use_case()

    async def handle(
        self, user_id: UserId, request: GetReceiptDetailRequest
    ) -> JSONResponse:
        result = await self._use_case.execute(
            user_id=user_id, receipt_uuid=request.receipt_uuid
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": 200,
                "data": result.to_dict(),
            },
        )
