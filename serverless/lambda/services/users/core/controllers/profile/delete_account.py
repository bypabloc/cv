"""Controller `profile.delete-account` — soft-delete self-service (AC-6/AC-29).

Requiere access JWT + el sentinel exacto `DELETE-MY-ACCOUNT` (validado por
el modelo Pydantic). Anonimiza el email, marca `deleted_at`, borra
credentials/mfa/recovery/webauthn/email_codes/magic_links + las sesiones, y
blacklistea todas las families del user. Guard AC-29: un admin (email en la
whitelist SSM) NO puede auto-borrarse.
"""

from __future__ import annotations

from typing import Any

from models.profile import ProfileDeleteAccountIn
from services.audit_service import AuditService
from services.email_dispatch_service import EmailDispatchService
from services.jwt_service import JwtService, require_active_user
from services.profile_service import ProfileService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.auth import is_admin
from shared.lambda_kit import BaseController
from shared.observability import MetricUnit, metrics

_ENDPOINT = '/users#profile.delete-account'


class DeleteAccount(BaseController):
    """Soft-delete self-service del propio user (action `delete-account`)."""

    event_model = ProfileDeleteAccountIn

    def validate(self) -> dict[str, Any]:
        """Pydantic (sentinel) + rate-limit per-IP."""
        base = super().validate()
        if not base.get('is_valid'):
            return base
        meta = self.validated_data.meta  # type: ignore[union-attr]
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '', endpoint=_ENDPOINT, country=meta.country,
        )
        return base

    def execute(self) -> dict[str, Any]:
        """Soft-delete + blacklist + notify.

        Returns:
            409 CANNOT_DELETE_ADMIN_ACCOUNT si el email es admin (AC-29).
            204 si la cuenta se borro.
        """
        data: ProfileDeleteAccountIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        user = require_active_user(meta.authorization, app_config=app_config)

        if is_admin(user.email):
            return {
                'is_valid': False,
                'code': 4009,
                'status': 409,
                'data': {
                    'error': 'CANNOT_DELETE_ADMIN_ACCOUNT',
                    'message': (
                        'Remueve tu email de la whitelist admin-emails '
                        'antes de borrar tu cuenta.'
                    ),
                },
            }

        old_email = user.email
        svc = ProfileService(app_config)
        families = svc.soft_delete(user_id=user.id)

        JwtService(app_config).revoke_families(
            family_ids=families, user_id=user.id,
        )
        EmailDispatchService(app_config).publish_account_deleted(
            to=old_email, user_id=user.id, niche=None,
        )
        AuditService(app_config).log(
            event='profile.delete-account',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )
        metrics.add_metric(
            name='UsersProfileDeleted', unit=MetricUnit.Count, value=1,
        )

        return {'is_valid': True, 'code': 0, 'status': 204, 'data': {}}
