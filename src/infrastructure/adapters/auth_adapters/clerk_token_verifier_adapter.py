from typing import Optional, Sequence

import httpx
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions

from src.config.logger import logger
from src.domain.entities.authenticated_user import AuthenticatedUser
from src.domain.errors.authentication_error import AuthenticationError
from src.domain.ports.token_verifier_port import TokenVerifierPort
from src.domain.value_objects.user_id import UserId


class ClerkTokenVerifier(TokenVerifierPort):
    """Verifica session tokens emitidos por Clerk.

    - Networkless si se configura `jwt_key`; si no, descarga el JWKS (el SDK lo
      cachea por `kid` y lo refresca cuando rota la llave).
    - `authorized_parties` restringe los orígenes (`azp`) aceptados para evitar
      reutilizar tokens de otro frontend.
    """

    def __init__(
        self,
        secret_key: str,
        *,
        authorized_parties: Optional[Sequence[str]] = None,
        audience: Optional[str] = None,
        accepts_token: Sequence[str] = ("session_token",),
    ) -> None:
        self._clerk = Clerk(bearer_auth=secret_key)
        self._secret_key = secret_key
        self._authorized_parties = (
            list(authorized_parties) if authorized_parties else None
        )
        self._audience = audience
        self._accepts_token = list(accepts_token)

    async def verify(self, bearer_token: str) -> AuthenticatedUser:
        state = await self._clerk.authenticate_request_async(
            self._build_request(bearer_token), self._build_options()
        )

        if not state.is_signed_in or not state.payload:
            logger.warning(f"Clerk rechazó el token: {state.reason}")
            raise AuthenticationError("Token de sesión inválido o expirado")

        subject = state.payload.get("sub")
        if not subject:
            raise AuthenticationError("El token no contiene el claim 'sub'")

        # El session token por defecto NO incluye `email`; si no se agregó como
        # custom claim en el dashboard de Clerk se consulta el Backend API.
        email = state.payload.get("email") or await self._get_primary_email(subject)
        if not email:
            raise AuthenticationError(
                "No se pudo resolver el email del usuario autenticado"
            )

        return AuthenticatedUser(user_id=UserId(subject), email=email)

    def _build_request(self, bearer_token: str) -> httpx.Request:
        """Request mínima: el SDK solo necesita el header Authorization."""
        return httpx.Request(
            "GET",
            "http://internal/",
            headers={"Authorization": f"Bearer {bearer_token}"},
        )

    def _build_options(self) -> AuthenticateRequestOptions:
        return AuthenticateRequestOptions(
            secret_key=self._secret_key,
            audience=self._audience,
            authorized_parties=self._authorized_parties,
            accepts_token=self._accepts_token,
        )

    async def _get_primary_email(self, user_id: str) -> Optional[str]:
        try:
            user = await self._clerk.users.get_async(user_id=user_id)
        except Exception as e:
            logger.warning(f"No se pudo obtener el usuario {user_id} de Clerk: {e}")
            return None

        email_addresses = user.email_addresses or []
        primary = next(
            (
                address
                for address in email_addresses
                if address.id == user.primary_email_address_id
            ),
            None,
        )
        if primary is None and email_addresses:
            primary = email_addresses[0]
        return primary.email_address if primary else None
