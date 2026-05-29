"""Controller `verify.set-password` — define la password tras verificar email.

El visitante (ya con el email verificado via magic-link o code) define
su password. Verifica el rolling temp_token (typ='temp'), hashea la
password con argon2id, la persiste en `auth_credentials`, blacklistea el
temp y emite access + refresh JWTs (cierra el flujo).

AC cubiertos: AC-4.
"""

from __future__ import annotations

from typing import Any

from models.verify import VerifySetPasswordIn
from services.audit_service import AuditService
from services.flow_service import FlowService
from services.jwt_service import JwtService
from services.rate_limit_service import RateLimitService
from services.user_service import UserService
from settings.config import app_config
from shared.auth import (
    JwtExpiredError,
    JwtInvalidError,
    JwtRevokedError,
    hash_password,
)
from shared.lambda_kit import BaseController

_ENDPOINT = '/auth#verify.set-password'


class SetPassword(BaseController):
    """Define la password del user (action `set-password`)."""

    event_model = VerifySetPasswordIn

    def validate(self) -> dict[str, Any]:
        """Pydantic (password min 12) + rate-limit. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: VerifySetPasswordIn = (
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
        """Verifica temp_token, hashea + persiste password, emite tokens.

        Returns:
            En exito: `{is_valid: True, code: 0, data: {access_token,
            refresh_token, user, ...}}`.
            temp_token expirado: 401 TEMP_TOKEN_EXPIRED (AC-18).
            temp_token blacklisted: 401 TOKEN_BLACKLISTED (AC-10).
        """
        data: VerifySetPasswordIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        jwt_svc = JwtService(app_config)
        flow_svc = FlowService(app_config)
        user_svc = UserService(app_config)
        audit_svc = AuditService(app_config)

        # El set-password puede venir de register o login: no fijamos
        # expected_flow, solo exigimos typ='temp' + no blacklisted.
        try:
            claims = jwt_svc.verify(data.temp_token, expected_typ='temp')
        except JwtExpiredError:
            audit_svc.log(
                event='verify.set-password',
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
                event='verify.set-password',
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
                event='verify.set-password',
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

        # Hashea + persiste la password (argon2id). El hashing ocurre en
        # el controller (CPU-bound, sin I/O); el service solo upserta.
        password_hash = hash_password(data.password)
        user_svc.set_password_hash(
            user_id=str(user.id),
            password_hash=password_hash,
        )

        # Cierra el flujo: blacklistea el temp + emite access + refresh.
        access_token, refresh_token, _ = flow_svc.terminate_flow(
            user_id=user.id,
            claims=claims,
        )

        audit_svc.log(
            event='verify.set-password',
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
