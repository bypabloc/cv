"""Controller `profile.confirm-email-change` — confirma el cambio (AC-5).

PUBLICO (sin Bearer): el user clickea el magic-link de su email NUEVO. Se
autentica por el token opaco single-use. Si el link es valido/vigente y el
nuevo email sigue libre: UPDATE `auth_users.email`, marca el link consumed,
notifica al email VIEJO y audita.
"""

from __future__ import annotations

from typing import Any

from models.profile import ProfileConfirmEmailChangeIn
from services.audit_service import AuditService
from services.email_dispatch_service import EmailDispatchService
from services.profile_service import ProfileService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/users#profile.confirm-email-change'


class ConfirmEmailChange(BaseController):
    """Confirma el cambio de email via el token del magic-link."""

    event_model = ProfileConfirmEmailChangeIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP (sin auth: token-based)."""
        base = super().validate()
        if not base.get('is_valid'):
            return base
        meta = self.validated_data.meta  # type: ignore[union-attr]
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '', endpoint=_ENDPOINT, country=meta.country,
        )
        return base

    def execute(self) -> dict[str, Any]:
        """Confirma el cambio de email.

        Returns:
            400 INVALID_OR_EXPIRED_LINK si el token es invalido/expirado/
            consumido o el nuevo email ya fue tomado.
            200 {confirmed, email} si el cambio se aplico.
        """
        data: ProfileConfirmEmailChangeIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta

        result = ProfileService(app_config).confirm_email_change(
            token=data.token,
        )
        if result is None:
            return {
                'is_valid': False,
                'code': 4007,
                'status': 400,
                'data': {'error': 'INVALID_OR_EXPIRED_LINK'},
            }

        user_id, old_email, new_email = result

        EmailDispatchService(app_config).publish_email_changed(
            to=old_email,
            user_id=user_id,
            niche=None,
            new_email=new_email,
        )
        AuditService(app_config).log(
            event='profile.change-email.confirmed',
            success=True,
            user_id=user_id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        return {
            'is_valid': True,
            'code': 0,
            'data': {'confirmed': True, 'email': new_email},
        }
