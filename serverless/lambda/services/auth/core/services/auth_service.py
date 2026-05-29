"""Auth helper service: resuelve el user autenticado de un request.

`require_active_user` extrae el access JWT del header
`Authorization: Bearer <X>` (inyectado por `http_handler` en
`data._meta.authorization`), lo verifica (signature + exp + typ +
blacklist via `JwtService`) y carga el `AuthUser` activo de Neon. Lo usan
los endpoints autenticados del plan 02 (`mfa.*`, `webauthn.*`).

Levanta `ApplicationError(status_code=401)` ante cualquier fallo; el
`http_handler` la traduce a una respuesta 401 `{error, code}`.
"""

from __future__ import annotations

from shared.auth import JwtError
from shared.core import ApplicationError
from shared.db import db_session
from shared.db.models import AuthUser, AuthUserStatus

from .jwt_service import JwtService


def require_active_user(
    authorization: str | None,
    *,
    app_config: object,
) -> AuthUser:
    """Devuelve el `AuthUser` activo del access JWT del header.

    Raises:
        ApplicationError(401): header ausente/mal formado, JWT invalido
        o revocado, o user inexistente/no activo.
    """
    if not authorization or not authorization.startswith('Bearer '):
        raise ApplicationError(
            'Missing Authorization header',
            code='MISSING_AUTHORIZATION',
            status_code=401,
        )
    raw = authorization.removeprefix('Bearer ').strip()

    jwt_svc = JwtService(app_config)
    try:
        claims = jwt_svc.verify(raw, expected_typ='access')
    except JwtError as exc:
        raise ApplicationError(
            'Invalid access token',
            code='TOKEN_INVALID',
            status_code=401,
        ) from exc

    with db_session() as session:
        user = session.get(AuthUser, str(claims.sub))
        if user is None or user.status != AuthUserStatus.ACTIVE:
            raise ApplicationError(
                'User not active',
                code='USER_NOT_ACTIVE',
                status_code=401,
            )
        return user
