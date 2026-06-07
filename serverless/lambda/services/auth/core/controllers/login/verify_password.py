"""Controller `login.verify-password` — `password` como metodo del checklist.

Plan login-mfa-list-redesign: la password es UN factor mas de la lista.
Recibe el `temp_token` step=2 (`flow='login-mfa[:...]'` emitido por
`login.start`) + `password`. Verifica el temp, valida la password con argon2,
suma `'password'` a los factores satisfechos y delega en `decide_mfa_step`:
- si quedan factores `required` pendientes -> rota un temp step=2 nuevo +
  `methods` (los faltantes).
- si ya estan todos -> emite access+refresh terminal.
Password incorrecta -> incrementa failed_attempts + 401 INVALID_PASSWORD.

AC cubiertos: AC-11, AC-16.
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
from shared.auth.jwt import JwtError
from shared.lambda_kit.base_controller import BaseController

from ._mfa_login import decide_mfa_step, parse_satisfied
from ._password_check import check_password

_ENDPOINT = '/auth#login.verify-password'
_MFA_FLOW = 'login-mfa'


class VerifyPassword(BaseController):
    """Valida la password como factor del checklist (action `verify-password`)."""

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
        """Verifica password + suma 'password' a satisfied + decide_mfa_step.

        Returns:
            401 TOKEN_INVALID si el temp no verifica o no es step=2 login-mfa.
            401 INVALID_PASSWORD + failed_attempts++ si no matchea.
            200 `{temp_token, methods, step:2, mfa_complete:false}` si faltan
            factores, o `{access_token, refresh_token, mfa_complete:true}` si
            ya estan todos (AC-11/AC-16).
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
            return self._token_invalid()

        # Debe ser un temp step=2 del checklist (flow 'login-mfa[:...]').
        flow_ok = (
            claims.flow is not None
            and claims.flow.split(':', 1)[0] == _MFA_FLOW
        )
        if not flow_ok or claims.step != 2:
            audit_svc.log(
                event='login.verify-password',
                success=False,
                error_code='TOKEN_INVALID',
                ip=meta.ip,
            )
            return self._token_invalid()

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

        # Password OK: blacklistea el temp step=2 recibido (rolling).
        jwt_svc.blacklist(
            jti=claims.jti,
            exp=claims.exp,
            user_id=user.id,
            reason='rotation',
        )

        # Suma 'password' a los factores satisfechos y delega en el motor.
        # `required` se pasa EXPLICITO (mockeable) para no acoplar el test a
        # la DB — mismo patron que verify_totp.
        satisfied = [*parse_satisfied(claims.flow), 'password']
        result = decide_mfa_step(
            jwt_svc=jwt_svc,
            app_config=app_config,
            user_id=user.id,
            satisfied=satisfied,
            required=mfa_svc.required_methods(user_id=user.id),
            ip=meta.ip,
            country=meta.country,
            user_agent=meta.user_agent,
        )
        if result.get('mfa_complete'):
            user_svc.update_last_login(user)
        audit_svc.log(
            event='login.verify-password',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )
        return {'is_valid': True, 'code': 0, 'data': result}

    @staticmethod
    def _token_invalid() -> dict[str, Any]:
        """Respuesta 401 TOKEN_INVALID."""
        return {
            'is_valid': False,
            'code': 4003,
            'status': 401,
            'data': {'error': 'TOKEN_INVALID'},
        }
