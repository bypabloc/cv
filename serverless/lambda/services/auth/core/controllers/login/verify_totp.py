"""Controller `login.verify-totp` — paso final del login con MFA TOTP.

Recibe un `temp_token` step=2 (flow='login-mfa', emitido tras un factor
fuerte) + `code` de 6 digitos. Verifica el TOTP confirmado del user y, si
OK, blacklistea el temp, marca last_used y emite access+refresh.

AC cubiertos: AC-19.
"""

from __future__ import annotations

from typing import Any

from models.login import LoginVerifyTotpIn
from services.audit_service import AuditService
from services.jwt_service import JwtService
from services.mfa_method_service import MfaMethodService
from services.rate_limit_service import RateLimitService
from services.totp_service import TotpService
from settings.config import app_config
from shared.auth.jwt import JwtError
from shared.db.models.auth import AuthMfaKind
from shared.lambda_kit.base_controller import BaseController

from ._mfa_login import issue_terminal_tokens

_ENDPOINT = '/auth#login.verify-totp'
_MFA_FLOW = 'login-mfa'
_MFA_STEP = 2


class VerifyTotp(BaseController):
    """Verifica el TOTP del login con MFA (action `verify-totp`)."""

    event_model = LoginVerifyTotpIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: LoginVerifyTotpIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '',
            endpoint=_ENDPOINT,
            country=meta.country,
            turnstile_validated=True,
        )
        return base

    def execute(self) -> dict[str, Any]:
        """Verifica el temp step=2 + el code TOTP; emite tokens.

        Returns:
            401 si el temp_token es invalido o no es step=2 login-mfa.
            400 MFA_NOT_CONFIGURED si el user no tiene TOTP confirmado.
            401 INVALID_TOTP_CODE si el code no matchea.
            200 `{access_token, refresh_token, ...}` si OK (AC-19).
        """
        data: LoginVerifyTotpIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta

        jwt_svc = JwtService(app_config)
        mfa_svc = MfaMethodService(app_config)
        totp_svc = TotpService(app_config)
        audit_svc = AuditService(app_config)

        try:
            claims = jwt_svc.verify(data.temp_token, expected_typ='temp')
        except JwtError:
            audit_svc.log(
                event='login.verify-totp',
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

        if claims.flow != _MFA_FLOW or claims.step != _MFA_STEP:
            return {
                'is_valid': False,
                'code': 4003,
                'status': 401,
                'data': {'error': 'TOKEN_INVALID'},
            }

        ciphertext = mfa_svc.get_totp_ciphertext(
            user_id=claims.sub,
            require_confirmed=True,
        )
        if ciphertext is None:
            return {
                'is_valid': False,
                'code': 4000,
                'status': 400,
                'data': {'error': 'MFA_NOT_CONFIGURED'},
            }

        ok = totp_svc.verify(
            user_id=claims.sub,
            ciphertext=ciphertext,
            code=data.code,
        )
        if not ok:
            audit_svc.log(
                event='login.verify-totp',
                success=False,
                user_id=claims.sub,
                error_code='INVALID_TOTP_CODE',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4008,
                'status': 401,
                'data': {'error': 'INVALID_TOTP_CODE'},
            }

        jwt_svc.blacklist(
            jti=claims.jti,
            exp=claims.exp,
            user_id=claims.sub,
            reason='rotation',
        )
        mfa_svc.mark_used(user_id=claims.sub, kind=AuthMfaKind.TOTP)
        tokens = issue_terminal_tokens(
            jwt_svc=jwt_svc,
            user_id=claims.sub,
            app_config=app_config,
            ip=meta.ip,
            country=meta.country,
            user_agent=meta.user_agent,
        )

        audit_svc.log(
            event='login.verify-totp',
            success=True,
            user_id=claims.sub,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        return {'is_valid': True, 'code': 0, 'data': tokens}
