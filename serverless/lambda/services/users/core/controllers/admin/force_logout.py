"""Controller `admin.force-logout` — cierra todas las sesiones (AC-18).

Requiere access JWT + admin. Borra todas las `auth_user_sessions` del
target + blacklistea cada family + audit row. 404 si el target no existe /
ya borrado. NO cambia el status del user (sigue activo, solo invalida sus
sesiones).
"""

from __future__ import annotations

from typing import Any

from models.admin import AdminForceLogoutIn
from services.admin_service import require_admin_user
from services.audit_admin_service import AuditAdminService
from services.jwt_service import JwtService, require_active_user
from services.profile_service import ProfileService
from services.rate_limit_service import RateLimitService
from services.session_service import SessionService
from settings.config import app_config
from shared.lambda_kit import BaseController
from shared.observability import MetricUnit, metrics

_ENDPOINT = '/users#admin'


class ForceLogout(BaseController):
    """Cierra todas las sesiones de un user (action `force-logout`)."""

    event_model = AdminForceLogoutIn

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
        """Revoca todas las sesiones + blacklist + audit.

        Returns:
            404 NOT_FOUND si el target no existe / ya borrado.
            204 si las sesiones se revocaron.
        """
        data: AdminForceLogoutIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        actor = require_active_user(meta.authorization, app_config=app_config)
        require_admin_user(
            actor, ip=meta.ip, user_agent=meta.user_agent,
            audit_action='admin.force-logout',
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

        reason = data.reason or 'admin discretion'
        AuditAdminService(app_config).log(
            admin_user_id=actor.id,
            target_user_id=target.id,
            action='force-logout',
            meta_data={'reason': reason},
            ip=meta.ip,
            user_agent=meta.user_agent,
        )
        families = SessionService(app_config).revoke_all_for_user(
            user_id=target.id,
        )
        JwtService(app_config).revoke_families(
            family_ids=families, user_id=target.id,
        )
        metrics.add_metric(
            name='UsersAdminAction', unit=MetricUnit.Count, value=1,
        )

        return {'is_valid': True, 'code': 0, 'status': 204, 'data': {}}
