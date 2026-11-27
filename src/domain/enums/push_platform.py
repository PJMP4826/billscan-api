from enum import Enum


class PushPlatform(str, Enum):
    """Plataforma del dispositivo que registra un token de notificaciones."""

    ANDROID = "android"
    IOS = "ios"
