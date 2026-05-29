"""Controller `login.verify-password` — paso 2a del login con password.

Variante 2-step: recibe un `temp_token` (de un login.start sin password)
+ `password`. Verifica el temp, valida la password con argon2 y:
- si el user NO tiene MFA -> emite access+refresh directo (AC-20).
- si el user TIENE MFA -> emite temp JWT step=2 flow='login-mfa' +
  methods=['totp','webauthn'] (AC-18). NUNCA incluye 'email-code'
  post-password (decision 10).
Password incorrecta -> incrementa failed_attempts + 401 INVALID_PASSWORD
(AC-21).

AC cubiertos: AC-18, AC-20, AC-21.
"""

from __future__ import annotations

from typing import Any

from models.login import LoginVerifyPasswordIn
from services.audit_service import AuditService
from services.jwt_service import JwtService
from services.mfa_method_service import MfaMethodService
from services.rate_limit_service import RateLimitService
from services.user_service import UserService
from settings.config import app_config
from shared.auth import JwtError
from shared.lambda_kit import BaseController

from ._mfa_login import issue_terminal_tokens
from ._password_check import check_password

_ENDPOINT = '/auth#login.verify-password'
_MFA_FLOW = 'login-mfa'
_MFA_METHODS = ['totp', 'webauthn']


class VerifyPassword(BaseController):
    """Valida la password tras login.start (action `verify-password`)."""

    event_model = LoginVerifyPasswordIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP (no por user_id, decision 13)."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: LoginVerifyPasswordIn = (
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
        """Verifica password + decide MFA step o login terminal.

        Returns:
            401 TOKEN_INVALID si el temp_token no verifica.
            401 INVALID_PASSWORD + failed_attempts++ si no matchea (AC-21).
            200 access+refresh si el user no tiene MFA (AC-20).
            200 temp step=2 + methods si el user tiene MFA (AC-18).
        """
        data: LoginVerifyPasswordIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        jwt_svc = JwtService(app_config)
        user_svc = UserService(app_config)
        mfa_svc = MfaMethodService(app_config)
        audit_svc = AuditService(app_config)

        try:
            claims = jwt_svc.verify(data.temp_token, expected_typ='temp')
        except JwtError:
            audit_svc.log(
                event='login.verify-password',
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

        user = user_svc.get_by_id(str(claims.sub))
        if user is None:
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'EMAIL_NOT_FOUND'},
            }

        if not check_password(user_id=user.id, password=data.password):
            user_svc.increment_failed_attempts(user)
            audit_svc.log(
                event='login.verify-password',
                success=False,
                user_id=user.id,
                error_code='INVALID_PASSWORD',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4000,
                'status': 401,
                'data': {'error': 'INVALID_PASSWORD'},
            }

        # Password OK: blacklistea el temp step=1 (rolling).
        jwt_svc.blacklist(
            jti=claims.jti,
            exp=claims.exp,
            user_id=user.id,
            reason='rotation',
        )

        if mfa_svc.count_active(user_id=user.id) == 0:
            tokens = issue_terminal_tokens(
                jwt_svc=jwt_svc,
                user_id=user.id,
                app_config=app_config,
                ip=meta.ip,
                country=meta.country,
                user_agent=meta.user_agent,
            )
            audit_svc.log(
                event='login.verify-password',
                success=True,
                user_id=user.id,
                ip=meta.ip,
                user_agent=meta.user_agent,
            )
            return {'is_valid': True, 'code': 0, 'data': tokens}

        temp_token, _ = jwt_svc.issue_temp(
            user_id=user.id,
            flow=_MFA_FLOW,
            step=2,
        )
        audit_svc.log(
            event='login.verify-password',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )
        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'temp_token': temp_token,
                'methods': list(_MFA_METHODS),
                'step': 2,
            },
        }
