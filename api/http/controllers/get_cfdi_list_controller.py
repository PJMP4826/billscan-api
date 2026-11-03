from fastapi import status
from fastapi.responses import JSONResponse

from src.bootstraps.use_cases_bootstrap import get_cfdi_list_use_case
from src.domain.value_objects.user_id import UserId


class GetCfdiListController:
    def __init__(self) -> None:
        self._use_case = get_cfdi_list_use_case()

    async def handle(
        self, user_id: UserId, page: int = 1, page_size: int = 20
    ) -> JSONResponse:
        try:
            result = await self._use_case.execute(user_id, page, page_size)

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": 200,
                    "data": result.to_dict(),
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
