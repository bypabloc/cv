"""JWT service del Lambda `analytics`.

Verifica el access JWT (HS256) del header `Authorization` y resuelve el
`AuthUser` activo de Neon. Portado del Lambda `users`
(`services/users/core/services/jwt_service.py`), simplificado: analytics es
read-only y NO maneja blacklist/revocacion de familias — solo necesita
`require_active_user` (verify + user activo) para cualquier user autenticado
(sin scope admin, Decision 1 del plan).

`require_active_user` distingue:
- header ausente / JWT invalido / expirado -> 401 (`code 4010`).
- user inexistente / soft-deleted / status no activo -> 401.
- user `disabled` -> 403 ACCOUNT_DISABLED; `locked` -> 403 ACCOUNT_LOCKED.

El secret se inyecta desde `AppConfig` (`jwt_secret`, lazy desde SSM); las
primitivas viven en `shared.auth.jwt` (portador de pyjwt). El `AuthUser` y
su enum de status vienen del modulo CONCRETO de `shared.db.models.auth`.
"""

from __future__ import annotations

from shared.auth.jwt import JwtError, verify_jwt
from shared.core.exceptions import ApplicationError
from shared.db.models.auth.enums import AuthUserStatus
from shared.db.models.auth.user import AuthUser
from shared.db.session import db_session


def authenticate(
    authorization: str | None,
    *,
    app_config: object,
) -> AuthUser:
    """Verifica el access JWT y devuelve el `AuthUser` activo.

    Args:
        authorization: header `Authorization` crudo (`Bearer <access JWT>`),
            inyectado por http_handler en `data._meta.authorization`.
        app_config: el AppConfig del Lambda (expone `jwt_secret`,
            `jwt_issuer`, `jwt_audience`).

    Raises:
        ApplicationError(401): header ausente/mal formado, JWT invalido o
            expirado, user inexistente / soft-deleted / status no activo.
        ApplicationError(403): user disabled (`ACCOUNT_DISABLED`) o locked
            (`ACCOUNT_LOCKED`) — el JWT es valido pero la cuenta esta
            bloqueada.
    """
    if not authorization or not authorization.startswith('Bearer '):
        raise ApplicationError(
            'Missing Authorization header',
            code='MISSING_AUTHORIZATION',
            status_code=401,
        )
    raw = authorization.removeprefix('Bearer ').strip()

    try:
        claims = verify_jwt(
            raw,
            secret=app_config.jwt_secret,  # type: ignore[attr-defined]
            expected_typ='access',
            audience=app_config.jwt_audience,  # type: ignore[attr-defined]
            issuer=app_config.jwt_issuer,  # type: ignore[attr-defined]
        )
    except JwtError as exc:
        raise ApplicationError(
            'Invalid access token',
            code='TOKEN_INVALID',
            status_code=401,
        ) from exc

    with db_session() as session:
        user = session.get(AuthUser, str(claims.sub))
        if user is None or user.deleted_at is not None:
            raise ApplicationError(
                'User not found',
                code='USER_NOT_ACTIVE',
                status_code=401,
            )
        if user.status == AuthUserStatus.DISABLED:
            raise ApplicationError(
                'Account disabled',
                code='ACCOUNT_DISABLED',
                status_code=403,
            )
        if user.status == AuthUserStatus.LOCKED:
            raise ApplicationError(
                'Account locked',
                code='ACCOUNT_LOCKED',
                status_code=403,
            )
        if user.status != AuthUserStatus.ACTIVE:
            raise ApplicationError(
                'User not active',
                code='USER_NOT_ACTIVE',
                status_code=401,
            )
        return user


def require_active_user(
    authorization: str | None,
    *,
    app_config: object,
) -> AuthUser:
    """Alias semantico de `authenticate` para los controllers.

    Cualquier user autenticado y activo puede leer las metricas (sin scope
    admin, Decision 1 del plan).
    """
    return authenticate(authorization, app_config=app_config)
