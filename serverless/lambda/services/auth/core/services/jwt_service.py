"""JWT service del Lambda `auth`.

Orquestador del lifecycle del JWT (HS256, SecureString + KMS en SSM):
- `issue_temp(user_id, flow, step)` -> rolling temp JWT (5 min).
- `issue_access(user_id)` -> access JWT stateless (15 min).
- `issue_refresh(user_id, family_id)` -> refresh JWT (30 dias) con
  rotation + family detection.
- `verify(token, expected_typ, expected_flow)` -> verifica signature
  + exp + aud + iss + typ (+ flow opcional) Y chequea blacklist
  contra DDB.

Las primitivas viven en `shared.auth.jwt`; aqui solo agregamos la
inyeccion del `secret` desde `AppConfig` y la verificacion de
blacklist via `BlacklistService`.
"""

from __future__ import annotations

from uuid import UUID

from shared.auth import (
    JwtClaims,
    JwtRevokedError,
    issue_access_jwt,
    issue_refresh_jwt,
    issue_temp_jwt,
    verify_jwt,
)
from shared.auth.jwt import JwtType

from .blacklist_service import BlacklistService


class JwtService:
    """Orquesta issue/verify del JWT y delega blacklist al BlacklistService."""

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

    def issue_temp(
        self, *, user_id: UUID | str, flow: str, step: int,
    ) -> tuple[str, JwtClaims]:
        """Emite un temp JWT (5 min) para rolling refresh entre pasos."""
        return issue_temp_jwt(
            user_id=UUID(str(user_id)),
            flow=flow,
            step=step,
            secret=self._secret,
            issuer=self._issuer,
            audience=self._audience,
        )

    def issue_access(
        self, *, user_id: UUID | str,
    ) -> tuple[str, JwtClaims]:
        """Emite un access JWT (15 min, stateless + blacklist DDB)."""
        return issue_access_jwt(
            user_id=UUID(str(user_id)),
            secret=self._secret,
            issuer=self._issuer,
            audience=self._audience,
        )

    def issue_refresh(
        self, *, user_id: UUID | str, family_id: UUID | str,
    ) -> tuple[str, JwtClaims]:
        """Emite un refresh JWT (30 dias) con `family_id` para reuse detect."""
        return issue_refresh_jwt(
            user_id=UUID(str(user_id)),
            family_id=UUID(str(family_id)),
            secret=self._secret,
            issuer=self._issuer,
            audience=self._audience,
        )

    def verify(
        self,
        token_str: str,
        *,
        expected_typ: JwtType | None = None,
        expected_flow: str | None = None,
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
        if expected_flow is not None and claims.flow != expected_flow:
            from shared.auth import JwtInvalidError
            raise JwtInvalidError(
                f'JWT flow mismatch: expected {expected_flow!r}, '
                f'got {claims.flow!r}',
            )
        # Blacklist check: si el jti esta en DDB -> revocado.
        if self._blacklist.is_blacklisted(jti=claims.jti):
            raise JwtRevokedError(f'JWT revoked: {claims.jti}')
        # Si es refresh, verificar tambien que la familia no este
        # revocada (token reuse detection).
        if claims.typ == 'refresh' and claims.family_id is not None:
            family_jtis = self._blacklist.query_family(
                family_id=claims.family_id,
            )
            if family_jtis:
                raise JwtRevokedError(
                    f'JWT family revoked: {claims.family_id}',
                )
        return claims

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
        """Marca toda la familia como revocada (token reuse detected)."""
        self._blacklist.revoke_family(
            family_id=family_id, user_id=user_id, exp=exp,
        )
