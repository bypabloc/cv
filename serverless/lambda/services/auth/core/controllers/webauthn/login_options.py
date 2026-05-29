"""Controller `webauthn.login-options` — opciones para login con passkey.

NO requiere auth (es un paso de login). Resuelve el user por email; si
no existe / no esta activo / no tiene credentials -> 404
NO_WEBAUTHN_CREDENTIALS (anti-enumeration: mismo body en los 3 casos).

AC cubiertos: AC-13.
"""

from __future__ import annotations

from typing import Any

from models.webauthn import WebauthnLoginOptionsIn
from services.challenge_service import ChallengeService
from services.rate_limit_service import RateLimitService
from services.user_service import UserService
from services.webauthn_service import WebauthnService
from settings.config import app_config
from shared.core.ulid import new_uuidv7
from shared.db.models import AuthUserStatus
from shared.lambda_kit import BaseController

_ENDPOINT = '/auth#webauthn.login-options'


class LoginOptions(BaseController):
    """Opciones de login con passkey (action `login-options`)."""

    event_model = WebauthnLoginOptionsIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: WebauthnLoginOptionsIn = (
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
        """Resuelve el user + genera el challenge de login.

        Returns:
            404 NO_WEBAUTHN_CREDENTIALS si el user no existe / no activo /
            sin credentials.
            200 `{challenge_id, options}` si tiene credentials.
        """
        data: WebauthnLoginOptionsIn = (
            self.validated_data  # type: ignore[assignment]
        )

        user_svc = UserService(app_config)
        webauthn_svc = WebauthnService(app_config)
        challenge_svc = ChallengeService(app_config)

        user = user_svc.get_by_email(data.email.lower())
        if user is None or user.status != AuthUserStatus.ACTIVE:
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'NO_WEBAUTHN_CREDENTIALS'},
            }
        if not webauthn_svc.has_credentials(user_id=user.id):
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'NO_WEBAUTHN_CREDENTIALS'},
            }

        options, state = webauthn_svc.build_login_options(user_id=user.id)
        challenge_id = new_uuidv7()
        challenge_svc.put(
            challenge_id=challenge_id,
            user_id=user.id,
            kind='login',
            state=state,
        )

        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'challenge_id': str(challenge_id),
                'options': options,
            },
        }
