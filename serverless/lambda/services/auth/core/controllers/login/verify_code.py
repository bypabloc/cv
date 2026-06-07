"""Controller `login.verify-code` — code 8 chars (factor de la lista).

Verifica el code de 8 chars que llego al email. Tiene DOS modos segun el
`step` del temp (plan login-mfa-list-redesign):

- **step=1** (`flow='login'`): code de ENTRADA passwordless (alta / pending /
  active sin otros required). Es el factor `passwordless`. Si el user no tiene
  mas factores required -> emite tokens directo (AC-15). Si SI los tiene
  (active con required que incluye el factor email) -> satisface el factor y
  delega en `decide_mfa_step` (los otros required siguen pendientes, AC-14).
- **step=2** (`flow='login-mfa[:...]'`): el code es UN factor mas del checklist
  (`passwordless` si es el unico, o `email_code` si el user lo marco MFA).
  Suma ese factor a los satisfechos y delega en `decide_mfa_step` (AC-13).

Marca `active` al user pending (cierra el alta) y `last_login_at`.

AC cubiertos: AC-13, AC-14, AC-15.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from models.login import LoginVerifyCodeIn
from services.audit_service import AuditService
from services.code_service import CodeService
from services.flow_service import FlowService
from services.jwt_service import JwtService
from services.mfa_method_service import MfaMethodService
from services.rate_limit_service import RateLimitService
from services.user_service import UserService
from settings.config import app_config
from shared.auth.jwt import JwtExpiredError, JwtInvalidError, JwtRevokedError
from shared.db.models.auth.enums import AuthCodeKind, AuthUserStatus
from shared.lambda_kit.base_controller import BaseController

from ._mfa_login import decide_mfa_step, parse_satisfied

_ENDPOINT = '/auth#login.verify-code'
_LOCK_DURATION = timedelta(hours=1)
_MAX_FAILED_ATTEMPTS = 5
# Los dos factores "code al email" del modelo de lista. En un checklist dado
# solo UNO esta presente (compose_required nunca pone ambos): `passwordless`
# (fallback unico) o `email_code` (metodo MFA explicito).
_EMAIL_FACTORS = ('passwordless', 'email_code')


def _email_factor(required: list[str]) -> str:
    """Devuelve el factor 'code al email' presente en `required`.

    Default `'passwordless'` (el caso de entrada / alta). Si el user marco
    `email_code` como MFA required, ese es el factor.
    """
    for factor in _EMAIL_FACTORS:
        if factor in required:
            return factor
    return 'passwordless'


class VerifyCode(BaseController):
    """Verifica el code de login (action `verify-code`)."""

    event_model = LoginVerifyCodeIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: LoginVerifyCodeIn = (
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
        """Verifica temp + code; emite tokens o delega en decide_mfa_step."""
        data: LoginVerifyCodeIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        flow_svc = FlowService(app_config)
        user_svc = UserService(app_config)
        code_svc = CodeService(app_config)
        jwt_svc = JwtService(app_config)
        mfa_svc = MfaMethodService(app_config)
        audit_svc = AuditService(app_config)

        # Acepta el temp de entrada (flow='login' step=1) O el del checklist
        # (flow='login-mfa[:...]' step=2). El `expected_flow=None` no fuerza el
        # flow aqui; abajo se distingue por `claims.step`.
        try:
            claims = flow_svc.verify_temp_token(
                data.temp_token,
                expected_flow=None,
            )
        except JwtExpiredError:
            audit_svc.log(
                event='login.verify-code',
                success=False,
                error_code='TEMP_TOKEN_EXPIRED',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4018,
                'status': 401,
                'data': {'error': 'TEMP_TOKEN_EXPIRED'},
            }
        except JwtRevokedError:
            audit_svc.log(
                event='login.verify-code',
                success=False,
                error_code='TOKEN_BLACKLISTED',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4003,
                'status': 401,
                'data': {'error': 'TOKEN_BLACKLISTED'},
            }
        except JwtInvalidError:
            audit_svc.log(
                event='login.verify-code',
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

        matched = code_svc.verify(
            user=user,
            kind=AuthCodeKind.LOGIN,
            code=data.code,
        )
        if not matched:
            attempts = user_svc.increment_failed_attempts(user)
            if attempts >= _MAX_FAILED_ATTEMPTS:
                until = datetime.now(tz=UTC) + _LOCK_DURATION
                user_svc.lock_user(user, until=until)
                audit_svc.log(
                    event='login.verify-code',
                    success=False,
                    user_id=user.id,
                    error_code='ACCOUNT_LOCKED',
                    ip=meta.ip,
                )
                return {
                    'is_valid': False,
                    'code': 4005,
                    'status': 423,
                    'data': {
                        'error': 'ACCOUNT_LOCKED',
                        'retry_after_seconds': int(
                            _LOCK_DURATION.total_seconds(),
                        ),
                    },
                }
            audit_svc.log(
                event='login.verify-code',
                success=False,
                user_id=user.id,
                error_code='INVALID_CODE',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4008,
                'status': 400,
                'data': {
                    'error': 'INVALID_CODE',
                    'attempts': attempts,
                },
            }

        # Fusion register -> login (bloque D): si el user es nuevo (pending),
        # el code valido cierra el registro -> lo marca active. Si ya esta
        # active, solo loguea. El backend decide por el STATUS, no por el flow.
        if user.status == AuthUserStatus.PENDING:
            user_svc.mark_active(user)

        # Code OK: blacklistea el temp recibido (rolling).
        jwt_svc.blacklist(
            jti=claims.jti,
            exp=claims.exp,
            user_id=user.id,
            reason='rotation',
        )

        # El factor "code al email" satisfecho: `passwordless` (entrada /
        # fallback) o `email_code` (metodo MFA explicito). Se suma a los
        # satisfechos del flow y se delega en decide_mfa_step, que decide si
        # quedan factores required pendientes (temp nuevo) o emite tokens.
        required = mfa_svc.required_methods(user_id=user.id)
        factor = _email_factor(required)
        satisfied = [*parse_satisfied(claims.flow), factor]
        result = decide_mfa_step(
            jwt_svc=jwt_svc,
            app_config=app_config,
            user_id=user.id,
            satisfied=satisfied,
            required=required,
            ip=meta.ip,
            country=meta.country,
            user_agent=meta.user_agent,
        )
        if result.get('mfa_complete'):
            user_svc.update_last_login(user)
            result = {
                **result,
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'status': user.status.value,
                },
            }

        audit_svc.log(
            event='login.verify-code',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        return {'is_valid': True, 'code': 0, 'data': result}
