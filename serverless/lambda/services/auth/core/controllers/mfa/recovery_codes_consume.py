"""Controller `mfa.recovery-codes-consume` — bypass MFA con un recovery code.

NO usa `require_active_user`: el user aun no tiene access JWT (esta en
medio del login). Verifica el `temp_token` step=2 emitido tras un factor
fuerte (password / webauthn). Si el factor previo es debil (magic-link /
email-code), rechaza con 403 RECOVERY_REQUIRES_STRONG_FACTOR (AC-9b).

Gate del factor fuerte: el temp JWT step=2 producido tras password lleva
`flow='login-mfa'`. Los flujos passwordless (magic-link / email-code)
NUNCA emiten un step=2 con ese flow, asi que el gate los excluye. Ver
nota de desviacion: JwtClaims tiene `extra='forbid'` y no admite un claim
`prev`; el flow codifica el factor previo.

AC cubiertos: AC-9, AC-9b, AC-10, AC-22.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from models.mfa import MfaRecoveryCodesConsumeIn
from services.audit_service import AuditService
from services.jwt_service import JwtService
from services.rate_limit_service import RateLimitService
from services.recovery_codes_service import RecoveryCodesService
from services.session_tracking_service import SessionTrackingService
from settings.config import app_config
from shared.auth.jwt import JwtError
from shared.core.ulid import new_uuidv7
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#mfa.recovery-codes-consume'
# El temp JWT step=2 producido tras un factor FUERTE (password / webauthn)
# usa este flow. magic-link / email-code nunca lo emiten (decision 10).
_STRONG_FLOW = 'login-mfa'
_STRONG_STEP = 2


class RecoveryCodesConsume(BaseController):
    """Consume un recovery code y emite tokens (action `recovery-codes-consume`)."""

    event_model = MfaRecoveryCodesConsumeIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: MfaRecoveryCodesConsumeIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '',
            endpoint=_ENDPOINT,
            country=meta.country,
            turnstile_validated=True,
        )
        return base

    def execute(self) -> dict[str, Any]:
        """Verifica el temp step=2 fuerte + consume el code; emite tokens.

        Returns:
            401 si el temp_token es invalido.
            403 RECOVERY_REQUIRES_STRONG_FACTOR si el factor previo no es
            fuerte (AC-9b).
            400 RECOVERY_CODE_CONSUMED si el code ya fue usado (AC-10).
            200 `{access_token, refresh_token, ...}` si OK (AC-9, AC-22).
        """
        data: MfaRecoveryCodesConsumeIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        jwt_svc = JwtService(app_config)
        recovery_svc = RecoveryCodesService(app_config)
        audit_svc = AuditService(app_config)

        try:
            claims = jwt_svc.verify(data.temp_token, expected_typ='temp')
        except JwtError:
            audit_svc.log(
                event='mfa.recovery-codes-consume',
                success=False,
                error_code='TOKEN_INVALID',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4003,
                'status': 401,
                'data': {'error': 'TOKEN_INVALID'},
            }

        if claims.flow != _STRONG_FLOW or claims.step != _STRONG_STEP:
            audit_svc.log(
                event='mfa.recovery-codes-consume',
                success=False,
                user_id=claims.sub,
                error_code='RECOVERY_REQUIRES_STRONG_FACTOR',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4000,
                'status': 403,
                'data': {'error': 'RECOVERY_REQUIRES_STRONG_FACTOR'},
            }

        consumed = recovery_svc.consume(user_id=claims.sub, code=data.code)
        if not consumed:
            audit_svc.log(
                event='mfa.recovery-codes-consume',
                success=False,
                user_id=claims.sub,
                error_code='RECOVERY_CODE_CONSUMED',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4008,
                'status': 400,
                'data': {'error': 'RECOVERY_CODE_CONSUMED'},
            }

        # Code OK: blacklistea el temp + emite access+refresh con family nuevo.
        jwt_svc.blacklist(
            jti=claims.jti,
            exp=claims.exp,
            user_id=claims.sub,
            reason='rotation',
        )
        family_id = UUID(new_uuidv7())
        access_token, _ = jwt_svc.issue_access(
            user_id=claims.sub, family_id=family_id,
        )
        refresh_token, _ = jwt_svc.issue_refresh(
            user_id=claims.sub,
            family_id=family_id,
        )
        SessionTrackingService(app_config).on_session_created(
            user_id=claims.sub,
            family_id=family_id,
            ip=meta.ip,
            country=meta.country,
            user_agent=meta.user_agent,
        )

        audit_svc.log(
            event='mfa.recovery-codes-consume',
            success=True,
            user_id=claims.sub,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': 900,
            },
        }
