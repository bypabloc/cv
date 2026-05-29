"""Controller `login.verify-code` — login passwordless via code 8 chars.

Espejo de `register.verify-code` pero con `expected_flow='login'` y
sin marcar al user como `active` (ya lo esta). Actualiza
`last_login_at` (AC-22) y emite access + refresh.

AC cubiertos: AC-22.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from models.login import LoginVerifyCodeIn
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

_ENDPOINT = '/auth#login.verify-code'
_LOCK_DURATION = timedelta(hours=1)
_MAX_FAILED_ATTEMPTS = 5


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
        """Verifica temp_token (flow='login') + code, emite access+refresh."""
        data: LoginVerifyCodeIn = (
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
                expected_flow='login',
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

        # Code OK: actualiza last_login + blacklistea el temp + tokens.
        user_svc.update_last_login(user)
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
            event='login.verify-code',
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
