from fastapi import status
from fastapi.responses import JSONResponse

from api.http.requests.get_receipt_detail_request import GetReceiptDetailRequest
from src.bootstraps.use_cases_bootstrap import get_receipt_detail_use_case
from src.shared.errors.base_exception import NotFoundError


class GetReceiptDetailController:
    def __init__(self) -> None:
        self._use_case = get_receipt_detail_use_case()

    async def handle(self, request: GetReceiptDetailRequest) -> JSONResponse:
        try:
            result = await self._use_case.execute(receipt_uuid=request.receipt_uuid)

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": 200,
                    "data": result,
                },
            )

        except NotFoundError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "title": "NOT FOUND",
                    "status": 404,
                    "message": e.get_message(),
                },
            )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "title": "NOT FOUND",
                    "status": 404,
                    "message": "Ticket no encontrado",
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
