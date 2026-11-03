from fastapi import status
from fastapi.responses import JSONResponse

from src.bootstraps.use_cases_bootstrap import get_user_regimens_use_case
from src.domain.value_objects.user_id import UserId
from src.shared.errors.base_exception import NotFoundError


class GetUserRegimensController:
    """Devuelve los regímenes fiscales del usuario para que el cliente elija.

    El cliente debe mostrar esta lista en su UI antes de enviar el ticket,
    porque el régimen con el que se factura se envía en la request.
    """

    def __init__(self) -> None:
        self._use_case = get_user_regimens_use_case()

    async def handle(self, user_id: UserId) -> JSONResponse:
        try:
            data = await self._use_case.execute(user_id=user_id)
            return JSONResponse(
                status_code=status.HTTP_200_OK, content={"status": 200, "data": data}
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
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "title": "Internal Server Error",
                    "status": 500,
                    "message": str(e),
                },
            )
