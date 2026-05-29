"""Controller `admin.disable-user` — deshabilita un user (AC-15).

Requiere access JWT + admin. UPDATE status=disabled + audit row pre-hoc +
notifica al user. 404 si el target no existe / ya borrado. 400 si el admin
intenta deshabilitarse a si mismo.
"""

from __future__ import annotations

from typing import Any

from models.admin import AdminDisableUserIn
from services.admin_service import require_admin_user
from services.audit_admin_service import AuditAdminService
from services.email_dispatch_service import EmailDispatchService
from services.jwt_service import require_active_user
from services.profile_service import ProfileService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.lambda_kit import BaseController
from shared.observability import MetricUnit, metrics

_ENDPOINT = '/users#admin'


class DisableUser(BaseController):
    """Deshabilita un user (action `disable-user`)."""

    event_model = AdminDisableUserIn

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
        """UPDATE status=disabled + audit + notify.

        Returns:
            404 NOT_FOUND si el target no existe / ya borrado.
            400 CANNOT_DISABLE_SELF si el admin se deshabilita a si mismo.
            204 si el user se deshabilito.
        """
        data: AdminDisableUserIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        actor = require_active_user(meta.authorization, app_config=app_config)
        require_admin_user(
            actor, ip=meta.ip, user_agent=meta.user_agent,
            audit_action='admin.disable-user',
        )

        target_id = str(data.user_id)
        svc = ProfileService(app_config)
        target = svc.get_by_id(user_id=target_id)
        if target is None or target.deleted_at is not None:
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'NOT_FOUND'},
            }
        if str(target.id) == str(actor.id):
            return {
                'is_valid': False,
                'code': 4002,
                'status': 400,
                'data': {'error': 'CANNOT_DISABLE_SELF'},
            }

        reason = data.reason or 'admin discretion'
        AuditAdminService(app_config).log(
            admin_user_id=actor.id,
            target_user_id=target.id,
            action='disable',
            meta_data={'reason': reason},
            ip=meta.ip,
            user_agent=meta.user_agent,
        )
        svc.disable(user_id=target.id)
        EmailDispatchService(app_config).publish_account_disabled(
            to=target.email, user_id=target.id, niche=None, reason=reason,
        )
        metrics.add_metric(
            name='UsersAdminAction', unit=MetricUnit.Count, value=1,
        )

        return {'is_valid': True, 'code': 0, 'status': 204, 'data': {}}
