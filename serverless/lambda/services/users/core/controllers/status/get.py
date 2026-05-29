"""Controller `status.get` — estado del propio user + info MFA (AC-7).

Requiere access JWT. Devuelve status, mfa_configured, mfa_methods,
webauthn_count, recovery_codes_remaining, failed_attempts y locked_until.
"""

from __future__ import annotations

from typing import Any

from models.status import StatusGetIn
from services.jwt_service import require_active_user
from services.profile_service import ProfileService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.lambda_kit import BaseController

_ENDPOINT = '/users#status'


class Get(BaseController):
    """Devuelve el estado del propio user (action `get`)."""

    event_model = StatusGetIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP."""
        base = super().validate()
        if not base.get('is_valid'):
            return base
        meta = self.validated_data.meta  # type: ignore[union-attr]
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '', endpoint=_ENDPOINT, country=meta.country,
        )
        return base

    def execute(self) -> dict[str, Any]:
        """Retorna 200 con el estado + detalle MFA."""
        data: StatusGetIn = self.validated_data  # type: ignore[assignment]
        user = require_active_user(data.meta.authorization, app_config=app_config)
        mfa = ProfileService(app_config).mfa_summary(user_id=user.id)
        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'status': user.status.value,
                'mfa_configured': mfa['mfa_configured'],
                'mfa_methods': mfa['mfa_methods'],
                'webauthn_count': mfa['webauthn_count'],
                'recovery_codes_remaining': mfa['recovery_codes_remaining'],
                'failed_attempts': user.failed_attempts,
                'locked_until': (
                    user.locked_until.isoformat()
                    if user.locked_until is not None
                    else None
                ),
            },
        }
