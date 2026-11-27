from pydantic import BaseModel, ConfigDict, Field

from src.domain.enums.push_platform import PushPlatform


class PushTokenRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    token: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Token de notificaciones de Expo (ExponentPushToken[...])",
    )
    platform: PushPlatform = Field(
        ..., description="Plataforma del dispositivo (android o ios)"
    )
