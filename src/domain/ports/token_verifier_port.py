from abc import ABC, abstractmethod

from src.domain.entities.authenticated_user import AuthenticatedUser


class TokenVerifierPort(ABC):
    """Puerto de verificación de session tokens del proveedor de auth."""

    @abstractmethod
    async def verify(self, bearer_token: str) -> AuthenticatedUser:
        """Valida el bearer token y devuelve la identidad autenticada.

        Lanza `AuthenticationError` si el token es inválido, expiró o fue
        emitido para otro origen/audiencia.
        """
        pass
