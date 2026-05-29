"""Controller `webauthn.login-verify` — valida la assertion + emite tokens.

NO requiere auth (es el cierre del login con passkey). Consume el
challenge, valida la assertion (signature + sign_count monotonico). Si el
sign_count regreso -> clone detected (el service deshabilita el credential
y re-lanza). Si OK, emite access+refresh con family nuevo.

AC cubiertos: AC-14, AC-15.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from models.webauthn import WebauthnLoginVerifyIn
from services.audit_service import AuditService
from services.challenge_service import ChallengeService
from services.jwt_service import JwtService
from services.rate_limit_service import RateLimitService
from services.webauthn_service import WebauthnService
from settings.config import app_config
from shared.auth import WebauthnCloneError, WebauthnVerifyError
from shared.core.ulid import new_uuidv7
from shared.lambda_kit import BaseController

_ENDPOINT = '/auth#webauthn.login-verify'


class LoginVerify(BaseController):
    """Valida la assertion + emite tokens (action `login-verify`)."""

    event_model = WebauthnLoginVerifyIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: WebauthnLoginVerifyIn = (
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
        """Consume el challenge + valida la assertion + emite tokens.

        Returns:
            400 WEBAUTHN_CHALLENGE_NOT_FOUND si el challenge no existe.
            401 WEBAUTHN_CLONE_DETECTED si el sign_count regreso (AC-15).
            401 WEBAUTHN_VERIFY_FAILED si la assertion es invalida.
            200 `{access_token, refresh_token, ...}` si OK (AC-14).
        """
        data: WebauthnLoginVerifyIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        jwt_svc = JwtService(app_config)
        webauthn_svc = WebauthnService(app_config)
        challenge_svc = ChallengeService(app_config)
        audit_svc = AuditService(app_config)

        challenge = challenge_svc.get_and_consume(
            challenge_id=data.challenge_id,
        )
        if challenge is None:
            return {
                'is_valid': False,
                'code': 4007,
                'status': 400,
                'data': {'error': 'WEBAUTHN_CHALLENGE_NOT_FOUND'},
            }

        user_id = challenge['user_id']
        try:
            webauthn_svc.verify_login(
                user_id=user_id,
                state=challenge['state'],
                response=data.response,
            )
        except WebauthnCloneError:
            audit_svc.log(
                event='webauthn.login.clone_detected',
                success=False,
                user_id=user_id,
                error_code='WEBAUTHN_CLONE_DETECTED',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4004,
                'status': 401,
                'data': {'error': 'WEBAUTHN_CLONE_DETECTED'},
            }
        except WebauthnVerifyError:
            audit_svc.log(
                event='webauthn.login-verify',
                success=False,
                user_id=user_id,
                error_code='WEBAUTHN_VERIFY_FAILED',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4004,
                'status': 401,
                'data': {'error': 'WEBAUTHN_VERIFY_FAILED'},
            }

        access_token, _ = jwt_svc.issue_access(user_id=user_id)
        family_id = UUID(new_uuidv7())
        refresh_token, _ = jwt_svc.issue_refresh(
            user_id=user_id,
            family_id=family_id,
        )

        audit_svc.log(
            event='webauthn.login.success',
            success=True,
            user_id=user_id,
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
