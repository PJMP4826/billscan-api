from fastapi import status
from fastapi.responses import JSONResponse

from src.bootstraps.use_cases_bootstrap import get_receipt_list_use_case
from src.domain.value_objects.user_id import UserId


class GetReceiptListController:
    def __init__(self) -> None:
        self._use_case = get_receipt_list_use_case()

    async def handle(
        self, user_id: UserId, page: int = 1, page_size: int = 20
    ) -> JSONResponse:
        result = await self._use_case.execute(user_id, page, page_size)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": 200,
                "data": result.to_dict(),
            },
        )
