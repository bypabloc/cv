"""JWT service del Lambda `cv` (operations admin).

Verifica el access JWT (HS256) del header `Authorization` y resuelve el
`AuthUser` activo de Neon. Portado del Lambda `users`
(`services/users/core/services/jwt_service.py`), simplificado: el cv
NO emite tokens ni revoca familias — solo necesita `require_active_user`
(verify + blacklist lookup + user activo) como primera capa de TODAS las
actions (la segunda es el scope admin, ver `admin_guard`).

`require_active_user` distingue:
- header ausente / JWT invalido / expirado / revocado -> 401.
- user inexistente / soft-deleted / status no activo -> 401.
- user `disabled` -> 403 ACCOUNT_DISABLED; `locked` -> 403 ACCOUNT_LOCKED.

El secret se inyecta desde `AppConfig` (`jwt_secret`, lazy desde SSM); las
primitivas viven en `shared.auth.jwt` (portador de pyjwt). El lookup de la
blacklist es read-only sobre la tabla DDB `jwt-blacklist`.
"""

from __future__ import annotations

from typing import Any

from shared.auth.jwt import JwtError, JwtRevokedError, verify_jwt
from shared.aws.dynamodb import get_table
from shared.core.exceptions import ApplicationError
from shared.db.models.auth.enums import AuthUserStatus
from shared.db.models.auth.user import AuthUser
from shared.db.session import db_session


def _is_blacklisted(jti: Any, *, app_config: object) -> bool:
    """True si el jti del access JWT esta en la blacklist DDB."""
    table_name = app_config.jwt_blacklist_table_name  # type: ignore[attr-defined]
    resp = get_table(table_name).get_item(
        Key={'jti': str(jti)},
        ConsistentRead=False,
    )
    return resp.get('Item') is not None


def authenticate(
    authorization: str | None,
    *,
    app_config: object,
) -> AuthUser:
    """Verifica el access JWT (firma + blacklist) y devuelve el user activo.

    Args:
        authorization: header `Authorization` crudo (`Bearer <access JWT>`),
            inyectado por http_handler en `data._meta.authorization`.
        app_config: el AppConfig del Lambda (expone `jwt_secret`,
            `jwt_issuer`, `jwt_audience`, `jwt_blacklist_table_name`).

    Raises:
        ApplicationError(401): header ausente/mal formado, JWT invalido,
            expirado o revocado, user inexistente / soft-deleted / status
            no activo.
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
        if _is_blacklisted(claims.jti, app_config=app_config):
            raise JwtRevokedError(f'JWT revoked: {claims.jti}')
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

    Primera capa de TODAS las actions de las operations admin del cv. El scope admin se
    valida despues con `admin_guard.require_admin_user`.
    """
    return authenticate(authorization, app_config=app_config)
