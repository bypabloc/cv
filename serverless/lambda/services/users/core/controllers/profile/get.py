"""Controller `profile.get` — devuelve el perfil del propio user (AC-1).

Requiere access JWT valido. NO devuelve password_hash, TOTP secret ni
info sensible: solo el perfil + un flag `mfa_configured`.
"""

from __future__ import annotations

from typing import Any

from models.profile import ProfileGetIn
from services.jwt_service import require_active_user
from services.profile_service import ProfileService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.lambda_kit import BaseController

_ENDPOINT = '/users#profile.get'


class Get(BaseController):
    """Devuelve el perfil del propio user (action `get`)."""

    event_model = ProfileGetIn

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
        """Retorna 200 con el perfil + mfa_configured."""
        data: ProfileGetIn = self.validated_data  # type: ignore[assignment]
        user = require_active_user(data.meta.authorization, app_config=app_config)
        mfa = ProfileService(app_config).mfa_summary(user_id=user.id)
        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'id': str(user.id),
                'email': user.email,
                'display_name': user.display_name,
                'locale': user.locale,
                'timezone': user.timezone,
                'marketing_consent': user.marketing_consent,
                'status': user.status.value,
                'created_at': user.created_at.isoformat(),
                'email_verified_at': (
                    user.email_verified_at.isoformat()
                    if user.email_verified_at is not None
                    else None
                ),
                'mfa_configured': mfa['mfa_configured'],
            },
        }
