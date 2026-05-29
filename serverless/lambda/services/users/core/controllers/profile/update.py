"""Controller `profile.update` — actualiza campos del propio user (AC-2/AC-3).

Requiere access JWT. Acepta parcial: cualquier subset de {display_name,
locale, timezone, marketing_consent, privacy_policy_version}. Si
`marketing_consent` cambia de valor -> INSERT en auth_user_consent_log
(GDPR).
"""

from __future__ import annotations

from typing import Any

from models.profile import ProfileUpdateIn
from services.audit_service import AuditService
from services.consent_service import ConsentService
from services.jwt_service import require_active_user
from services.profile_service import ProfileService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.lambda_kit import BaseController
from shared.observability import MetricUnit, metrics

_ENDPOINT = '/users#profile.update'
_EDITABLE = (
    'display_name',
    'locale',
    'timezone',
    'marketing_consent',
    'privacy_policy_version',
)


class Update(BaseController):
    """Actualiza el perfil del propio user (action `update`)."""

    event_model = ProfileUpdateIn

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
        """Actualiza los campos enviados + loggea consent si cambio."""
        data: ProfileUpdateIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        user = require_active_user(meta.authorization, app_config=app_config)

        updates = {
            field: getattr(data, field)
            for field in _EDITABLE
            if getattr(data, field) is not None
        }

        old_marketing = user.marketing_consent
        new_marketing = data.marketing_consent

        updated = ProfileService(app_config).update(
            user_id=user.id, **updates,
        )

        if new_marketing is not None and new_marketing != old_marketing:
            ConsentService(app_config).log(
                user_id=user.id,
                field='marketing_consent',
                old_value=str(old_marketing),
                new_value=str(new_marketing),
                ip=meta.ip,
                user_agent=meta.user_agent,
            )

        AuditService(app_config).log(
            event='profile.update',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
            meta_data={'fields': sorted(updates.keys())},
        )
        metrics.add_metric(
            name='UsersProfileUpdated', unit=MetricUnit.Count, value=1,
        )

        target = updated if updated is not None else user
        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'id': str(target.id),
                'email': target.email,
                'display_name': target.display_name,
                'locale': target.locale,
                'timezone': target.timezone,
                'marketing_consent': target.marketing_consent,
            },
        }
