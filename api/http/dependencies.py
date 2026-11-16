from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.use_cases.ensure_user_exists_use_case import (
    EnsureUserExistsUseCase,
)
from src.bootstraps.services.infrastructure_bootstrap_services import (
    get_token_verifier_adapter,
)
from src.bootstraps.use_cases_bootstrap import get_ensure_user_use_case
from src.config.logger import logger
from src.domain.entities.authenticated_user import AuthenticatedUser
from src.domain.errors.authentication_error import AuthenticationError
from src.domain.ports.token_verifier_port import TokenVerifierPort
from src.domain.value_objects.user_id import UserId

bearer = HTTPBearer(auto_error=False)


async def get_authenticated_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    verifier: TokenVerifierPort = Depends(get_token_verifier_adapter),
) -> AuthenticatedUser:
    """Valida el bearer token de Clerk y devuelve la identidad autenticada."""
    if creds is None:
        raise AuthenticationError(
            "Falta el encabezado Authorization",
            error_code="MISSING_AUTHORIZATION_HEADER",
        )

    try:
        return await verifier.verify(creds.credentials)
    except AuthenticationError as e:
        # El motivo técnico solo se loguea; al cliente no se le expone.
        logger.warning(f"Autenticación fallida: {e.get_message()}")
        raise AuthenticationError(
            "Token inválido o expirado",
            error_code="INVALID_TOKEN",
        ) from e


async def get_current_user_id(
    identity: AuthenticatedUser = Depends(get_authenticated_user),
    ensure_user: EnsureUserExistsUseCase = Depends(get_ensure_user_use_case),
) -> UserId:
    """Devuelve el `UserId` y garantiza que el usuario exista en la BD."""
    await ensure_user.execute(identity)
    return identity.user_id
