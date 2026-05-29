"""JWT service del Lambda `users`.

Verifica el access JWT (HS256) del header `Authorization` y resuelve el
`AuthUser` activo de Neon. A diferencia del Lambda `auth`, este NO emite
tokens (users no hace login) — solo `verify` + las operaciones de
blacklist (revoke-session / force-logout / delete-account).

`require_active_user` distingue (AC-16):
- header ausente / JWT invalido / revocado -> 401 (token problem).
- user `disabled` -> 403 ACCOUNT_DISABLED (JWT valido, cuenta bloqueada).
- user `locked` -> 403 ACCOUNT_LOCKED.
- user inexistente / soft-deleted / otro status -> 401.

El secret se inyecta desde `AppConfig`; las primitivas viven en
`shared.auth` (portador de pyjwt).
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from uuid import UUID

from shared.auth import (
    JwtClaims,
    JwtError,
    JwtRevokedError,
    verify_jwt,
)
from shared.auth.jwt import JwtType
from shared.core import ApplicationError
from shared.db import db_session
from shared.db.models import AuthUser, AuthUserStatus

from .blacklist_service import BlacklistService

# TTL del sentinela de revocacion de familia cuando no se conoce el `exp`
# real del refresh (revoke-session / force-logout / delete-account). 30
# dias = lifetime maximo del refresh, asi cubre cualquier token in-flight.
_REFRESH_TTL_SECONDS = 30 * 24 * 3600


class JwtService:
    """Verifica el JWT y delega blacklist al BlacklistService."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config
        self._blacklist = BlacklistService(app_config)

    @property
    def _secret(self) -> str:
        return self.app_config.jwt_secret  # type: ignore[attr-defined]

    @property
    def _issuer(self) -> str:
        return self.app_config.jwt_issuer  # type: ignore[attr-defined]

    @property
    def _audience(self) -> str:
        return self.app_config.jwt_audience  # type: ignore[attr-defined]

    def verify(
        self,
        token_str: str,
        *,
        expected_typ: JwtType | None = None,
    ) -> JwtClaims:
        """Verifica signature + exp + aud + iss + typ + blacklist.

        Raises:
            JwtExpiredError, JwtInvalidError, JwtRevokedError.
        """
        claims = verify_jwt(
            token_str,
            secret=self._secret,
            expected_typ=expected_typ,
            audience=self._audience,
            issuer=self._issuer,
        )
        if self._blacklist.is_blacklisted(jti=claims.jti):
            raise JwtRevokedError(f'JWT revoked: {claims.jti}')
        return claims

    def is_blacklisted(self, *, jti: UUID | str) -> bool:
        """True si el jti esta en la blacklist DDB."""
        return self._blacklist.is_blacklisted(jti=jti)

    def blacklist(
        self,
        *,
        jti: UUID | str,
        exp: int,
        user_id: UUID | str,
        reason: str,
        family_id: UUID | str | None = None,
    ) -> None:
        """Pone un jti en la blacklist (delega al BlacklistService)."""
        self._blacklist.put(
            jti=jti, exp=exp, user_id=user_id,
            reason=reason, family_id=family_id,
        )

    def revoke_family(
        self,
        *,
        family_id: UUID | str,
        user_id: UUID | str,
        exp: int,
    ) -> None:
        """Marca toda una familia de refresh como revocada."""
        self._blacklist.revoke_family(
            family_id=family_id, user_id=user_id, exp=exp,
        )

    def revoke_families(
        self,
        *,
        family_ids: Iterable[UUID | str],
        user_id: UUID | str,
    ) -> None:
        """Blacklistea cada family con TTL default (30 dias).

        Lo usan revoke-session / force-logout / delete-account, que no
        tienen el `exp` real del refresh de cada sesion.
        """
        exp = int(time.time()) + _REFRESH_TTL_SECONDS
        for family_id in family_ids:
            self._blacklist.revoke_family(
                family_id=family_id, user_id=user_id, exp=exp,
            )


def authenticate(
    authorization: str | None,
    *,
    app_config: object,
) -> tuple[AuthUser, JwtClaims]:
    """Verifica el access JWT y devuelve `(AuthUser activo, JwtClaims)`.

    Los `claims` exponen `family_id` (la sesion en curso) para que
    `status.*` marque la sesion actual y bloquee revocarla (AC-8/AC-10).

    Raises:
        ApplicationError(401): header ausente/mal formado, JWT invalido o
            revocado, user inexistente o soft-deleted.
        ApplicationError(403): user disabled (`ACCOUNT_DISABLED`) o locked
            (`ACCOUNT_LOCKED`) — el JWT es valido pero la cuenta esta
            bloqueada (AC-16).
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
        return user, claims


def require_active_user(
    authorization: str | None,
    *,
    app_config: object,
) -> AuthUser:
    """Como `authenticate` pero devuelve solo el `AuthUser` (sin claims).

    Lo usan los controllers de profile/admin que no necesitan el
    `family_id` de la sesion en curso.
    """
    user, _ = authenticate(authorization, app_config=app_config)
    return user
