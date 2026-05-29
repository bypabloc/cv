"""Controller `register.verify-code` — confirma con code 8 chars + temp_token.

El visitante pega el code que recibio por email. Verifica el rolling
temp_token (typ='temp', flow='register'), valida el code (constant-time
compare contra el hash en Neon, incrementa attempts, autobloquea al 5to
fallo) y, en exito, blacklistea el temp, activa al user y emite
access + refresh JWTs.

AC cubiertos: AC-4, AC-10, AC-11, AC-18.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from models.register import RegisterVerifyCodeIn
from services.audit_service import AuditService
from services.code_service import CodeService
from services.flow_service import FlowService
from services.jwt_service import JwtService
from services.rate_limit_service import RateLimitService
from services.session_tracking_service import SessionTrackingService
from services.user_service import UserService
from settings.config import app_config
from shared.auth.jwt import JwtExpiredError, JwtInvalidError, JwtRevokedError
from shared.core.ulid import new_uuidv7
from shared.db.models.auth import AuthCodeKind
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#register.verify-code'
_LOCK_DURATION = timedelta(hours=1)
_MAX_FAILED_ATTEMPTS = 5


class VerifyCode(BaseController):
    """Verifica el code de registro (action `verify-code`)."""

    event_model = RegisterVerifyCodeIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit (sin Turnstile, ya valido en start)."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: RegisterVerifyCodeIn = (
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
        """Verifica temp_token + code, emite access+refresh.

        Returns:
            En exito: `{is_valid: True, code: 0, data: {access_token,
            refresh_token, user, ...}}`.
            temp_token expirado: 401 TEMP_TOKEN_EXPIRED (AC-18).
            temp_token blacklisted: 401 TOKEN_BLACKLISTED (AC-10).
            code invalido: 400 INVALID_CODE (AC-11) o 423 ACCOUNT_LOCKED
            (>=5 fallos, AC-11).
        """
        data: RegisterVerifyCodeIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        flow_svc = FlowService(app_config)
        user_svc = UserService(app_config)
        code_svc = CodeService(app_config)
        jwt_svc = JwtService(app_config)
        audit_svc = AuditService(app_config)

        try:
            claims = flow_svc.verify_temp_token(
                data.temp_token,
                expected_flow='register',
            )
        except JwtExpiredError:
            audit_svc.log(
                event='register.verify-code',
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
                event='register.verify-code',
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
                event='register.verify-code',
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

        # Verifica el code; si wrong, code_svc / repository incrementan
        # `attempts` en el row. El controller chequea failed_attempts
        # del USER (no del code) para decidir el lock — politica AC-11.
        matched = code_svc.verify(
            user=user,
            kind=AuthCodeKind.REGISTER,
            code=data.code,
        )
        if not matched:
            attempts = user_svc.increment_failed_attempts(user)
            if attempts >= _MAX_FAILED_ATTEMPTS:
                until = datetime.now(tz=UTC) + _LOCK_DURATION
                user_svc.lock_user(user, until=until)
                audit_svc.log(
                    event='register.verify-code',
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
                event='register.verify-code',
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

        # Code OK: activa el user + blacklistea el temp + emite tokens.
        user_svc.mark_active(user)
        jwt_svc.blacklist(
            jti=claims.jti,
            exp=claims.exp,
            user_id=user.id,
            reason='rotation',
        )

        family_id = UUID(new_uuidv7())
        access_token, _ = jwt_svc.issue_access(
            user_id=user.id, family_id=family_id,
        )
        refresh_token, _ = jwt_svc.issue_refresh(
            user_id=user.id,
            family_id=family_id,
        )
        SessionTrackingService(app_config).on_session_created(
            user_id=user.id,
            family_id=family_id,
            ip=meta.ip,
            country=meta.country,
            user_agent=meta.user_agent,
        )

        audit_svc.log(
            event='register.verify-code',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': 900,
                'token_type': 'Bearer',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'status': user.status.value,
                },
            },
        }
