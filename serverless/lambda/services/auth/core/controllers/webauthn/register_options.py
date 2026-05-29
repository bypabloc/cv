"""Controller `webauthn.register-options` — opciones para registrar un passkey.

Requiere access JWT valido. Construye las options del ceremony
(navigator.credentials.create) + el state fido2, persiste el state en
DDB con TTL 5 min y devuelve `{challenge_id, options}`.

AC cubiertos: AC-11.
"""

from __future__ import annotations

from typing import Any

from models.webauthn import WebauthnRegisterOptionsIn
from services.auth_service import require_active_user
from services.challenge_service import ChallengeService
from services.rate_limit_service import RateLimitService
from services.webauthn_service import WebauthnService
from settings.config import app_config
from shared.core.ulid import new_uuidv7
from shared.lambda_kit import BaseController

_ENDPOINT = '/auth#webauthn.register-options'


class RegisterOptions(BaseController):
    """Opciones de registro de passkey (action `register-options`)."""

    event_model = WebauthnRegisterOptionsIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: WebauthnRegisterOptionsIn = (
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
        """Genera + persiste el challenge; devuelve options.

        Returns:
            200 `{challenge_id, options}`.
        """
        data: WebauthnRegisterOptionsIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)

        webauthn_svc = WebauthnService(app_config)
        challenge_svc = ChallengeService(app_config)

        options, state = webauthn_svc.build_register_options(
            user_id=user.id,
            user_name=user.email,
        )
        challenge_id = new_uuidv7()
        challenge_svc.put(
            challenge_id=challenge_id,
            user_id=user.id,
            kind='register',
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
