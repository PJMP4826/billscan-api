from fastapi import status
from fastapi.responses import JSONResponse

from src.bootstraps.use_cases_bootstrap import get_user_regimens_use_case
from src.domain.value_objects.user_id import UserId


class GetUserRegimensController:
    """Devuelve los regímenes fiscales del usuario para que el cliente elija.

    El cliente debe mostrar esta lista en su UI antes de enviar el ticket,
    porque el régimen con el que se factura se envía en la request.
    """

    def __init__(self) -> None:
        self._use_case = get_user_regimens_use_case()

    async def handle(self, user_id: UserId) -> JSONResponse:
        data = await self._use_case.execute(user_id=user_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"status": 200, "data": data}
        )
