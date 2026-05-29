"""Flow service del Lambda `auth`.

Orquestador del patron "rolling temp JWT" implementado en cada
controller del flujo (register.verify-magic-link, register.verify-code,
verify.set-password, verify.resend-code, login.verify-magic-link,
login.verify-code).

Estandariza 3 operaciones de alto nivel sobre el temp_token:
- `verify_temp_token(token, expected_flow)`: verifica + chequea
  blacklist + retorna `JwtClaims`.
- `advance_step(claims)`: blacklistea el jti viejo + emite un nuevo
  temp con `step+1`. Retorna (token_nuevo, claims_nuevos).
- `terminate_flow(user_id, claims)`: blacklistea el temp + emite
  access + refresh nuevos (con `family_id` nuevo). Retorna
  (access_token, refresh_token, family_id).

NO contiene logica de negocio del controller: solo el patron JWT que
todos los actions del flujo comparten.
"""

from __future__ import annotations

from uuid import UUID

from shared.auth import JwtClaims
from shared.core.ulid import new_uuidv7

from .jwt_service import JwtService
from .session_tracking_service import SessionTrackingService


class FlowService:
    """Patron rolling temp JWT compartido por los controllers del flujo."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config
        self._jwt = JwtService(app_config)

    def verify_temp_token(
        self, token_str: str, *, expected_flow: str,
    ) -> JwtClaims:
        """Verifica typ='temp' + flow esperado + blacklist."""
        return self._jwt.verify(
            token_str,
            expected_typ='temp',
            expected_flow=expected_flow,
        )

    def advance_step(self, claims: JwtClaims) -> tuple[str, JwtClaims]:
        """Blacklistea el jti viejo + emite un temp con step+1.

        El `flow` se preserva; `step` se incrementa. El blacklist usa
        `reason='rotation'`.
        """
        self._jwt.blacklist(
            jti=claims.jti,
            exp=claims.exp,
            user_id=claims.sub,
            reason='rotation',
        )
        next_step = (claims.step or 1) + 1
        return self._jwt.issue_temp(
            user_id=claims.sub,
            flow=claims.flow or '',
            step=next_step,
        )

    def terminate_flow(
        self,
        *,
        user_id: UUID | str,
        claims: JwtClaims,
        ip: str | None = None,
        country: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[str, str, UUID]:
        """Cierra el flujo: blacklistea el temp + emite access + refresh.

        El `family_id` nuevo (uuidv7) se embebe TANTO en el access (para que
        el Lambda `users` identifique la sesion en curso) COMO en el refresh
        (rotation). Si se pasan ip/country/user_agent, registra la sesion en
        `auth_user_sessions` (best-effort, mismo patron que el login con
        MFA). Retorna `(access_token, refresh_token, family_id)`.
        """
        self._jwt.blacklist(
            jti=claims.jti,
            exp=claims.exp,
            user_id=user_id,
            reason='rotation',
        )
        family_id = UUID(new_uuidv7())
        access_str, _ = self._jwt.issue_access(
            user_id=user_id, family_id=family_id,
        )
        refresh_str, _ = self._jwt.issue_refresh(
            user_id=user_id, family_id=family_id,
        )
        SessionTrackingService(self.app_config).on_session_created(
            user_id=user_id,
            family_id=family_id,
            ip=ip,
            country=country,
            user_agent=user_agent,
        )
        return access_str, refresh_str, family_id
