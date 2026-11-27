from fastapi import status
from fastapi.responses import JSONResponse

from api.http.requests.push_token_request import PushTokenRequest
from src.bootstraps.use_cases_bootstrap import get_register_push_token_use_case
from src.domain.value_objects.user_id import UserId


class RegisterPushTokenController:
    def __init__(self) -> None:
        self._use_case = get_register_push_token_use_case()

    async def handle(
        self, user_id: UserId, request_data: PushTokenRequest
    ) -> JSONResponse:
        await self._use_case.execute(
            user_id=user_id,
            token=request_data.token,
            platform=request_data.platform,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": 200,
                "message": "Token de notificación registrado",
            },
        )
