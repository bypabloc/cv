"""Controller `admin.delete-user` — hard-delete con cascada (AC-19).

Requiere access JWT + admin + el sentinel exacto
`HARD-DELETE-USER-<user_id>` (validado por el modelo). Borra todas las
filas relacionadas del target (auth_audit_log queda con user_id SET NULL)
+ blacklistea sus families + audit row + notifica. 404 si no existe. 400
si el admin intenta borrarse a si mismo.
"""

from __future__ import annotations

from typing import Any

from models.admin import AdminDeleteUserIn
from services.admin_service import require_admin_user
from services.audit_admin_service import AuditAdminService
from services.email_dispatch_service import EmailDispatchService
from services.jwt_service import JwtService, require_active_user
from services.profile_service import ProfileService
from services.rate_limit_service import RateLimitService
from services.session_service import SessionService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController
from shared.observability.metrics import MetricUnit, metrics

_ENDPOINT = '/users#admin'


class DeleteUser(BaseController):
    """Hard-delete de un user (action `delete-user`)."""

    event_model = AdminDeleteUserIn

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
        """Hard-delete + blacklist + audit + notify.

        Returns:
            404 NOT_FOUND si el target no existe.
            400 CANNOT_DELETE_SELF si el admin se borra a si mismo.
            204 si el user se borro.
        """
        data: AdminDeleteUserIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        actor = require_active_user(meta.authorization, app_config=app_config)
        require_admin_user(
            actor, ip=meta.ip, user_agent=meta.user_agent,
            audit_action='admin.delete-user',
        )

        target_id = str(data.user_id)
        svc = ProfileService(app_config)
        target = svc.get_by_id(user_id=target_id)
        if target is None:
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'NOT_FOUND'},
            }
        if str(target.id) == str(actor.id):
            return {
                'is_valid': False,
                'code': 4003,
                'status': 400,
                'data': {'error': 'CANNOT_DELETE_SELF'},
            }

        old_email = target.email
        # Audit PRE-hoc: el row referencia al target; el hard-delete luego
        # lo deja en NULL (FK SET NULL) preservando el audit.
        AuditAdminService(app_config).log(
            admin_user_id=actor.id,
            target_user_id=target.id,
            action='delete',
            ip=meta.ip,
            user_agent=meta.user_agent,
        )
        families = SessionService(app_config).revoke_all_for_user(
            user_id=target.id,
        )
        JwtService(app_config).revoke_families(
            family_ids=families, user_id=target.id,
        )
        EmailDispatchService(app_config).publish_account_deleted(
            to=old_email, user_id=target.id, niche=None,
        )
        svc.hard_delete(user_id=target.id)
        metrics.add_metric(
            name='UsersAdminAction', unit=MetricUnit.Count, value=1,
        )

        return {'is_valid': True, 'code': 0, 'status': 204, 'data': {}}
