"""Controller `admin.list-admin-actions` — historico de admin actions (AC-20).

Requiere access JWT + admin. Devuelve el historico paginado de
`auth_user_admin_actions` (metadata, IP, admin_user_id, target_user_id),
created_at DESC, filtrable por rango from_date/to_date.
"""

from __future__ import annotations

from typing import Any

from models.admin import AdminListAdminActionsIn
from services.admin_service import require_admin_user
from services.audit_admin_service import AuditAdminService
from services.jwt_service import require_active_user
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/users#admin'


class ListAdminActions(BaseController):
    """Historico de admin actions (action `list-admin-actions`)."""

    event_model = AdminListAdminActionsIn

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
        """Retorna 200 con la pagina de admin actions + next_cursor."""
        data: AdminListAdminActionsIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        actor = require_active_user(meta.authorization, app_config=app_config)
        require_admin_user(
            actor, ip=meta.ip, user_agent=meta.user_agent,
            audit_action='admin.list-admin-actions',
        )

        cursor = str(data.cursor) if data.cursor is not None else None
        actions = AuditAdminService(app_config).list_actions(
            from_date=data.from_date,
            to_date=data.to_date,
            page_size=data.page_size,
            cursor=cursor,
        )
        next_cursor = (
            actions[-1]['id'] if len(actions) == data.page_size else None
        )
        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'actions': actions,
                'next_cursor': next_cursor,
                'page_size': data.page_size,
                'total_returned': len(actions),
            },
        }
