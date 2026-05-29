"""Controller `admin.enable-user` — re-habilita un user (AC-17).

Requiere access JWT + admin. UPDATE status=active + audit row. 404 si el
target no existe / ya borrado. Idempotente (re-habilitar un user activo
devuelve 204 igual).
"""

from __future__ import annotations

from typing import Any

from models.admin import AdminEnableUserIn
from services.admin_service import require_admin_user
from services.audit_admin_service import AuditAdminService
from services.jwt_service import require_active_user
from services.profile_service import ProfileService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/users#admin'


class EnableUser(BaseController):
    """Re-habilita un user (action `enable-user`)."""

    event_model = AdminEnableUserIn

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
        """UPDATE status=active + audit.

        Returns:
            404 NOT_FOUND si el target no existe / ya borrado.
            204 si el user se habilito.
        """
        data: AdminEnableUserIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        actor = require_active_user(meta.authorization, app_config=app_config)
        require_admin_user(
            actor, ip=meta.ip, user_agent=meta.user_agent,
            audit_action='admin.enable-user',
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

        AuditAdminService(app_config).log(
            admin_user_id=actor.id,
            target_user_id=target.id,
            action='enable',
            ip=meta.ip,
            user_agent=meta.user_agent,
        )
        svc.enable(user_id=target.id)

        return {'is_valid': True, 'code': 0, 'status': 204, 'data': {}}
