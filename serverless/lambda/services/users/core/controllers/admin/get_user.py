"""Controller `admin.get-user` — detalle de un user (AC-14/AC-28).

Requiere access JWT + admin. Devuelve profile + resumen MFA + count de
sesiones + ultimos 10 eventos de audit. Si el target esta soft-deleted,
devuelve el row con `deleted_at` + email anonimizado (AC-28). NUNCA expone
password_hash ni TOTP secret.
"""

from __future__ import annotations

from typing import Any

from models.admin import AdminGetUserIn
from services.admin_service import require_admin_user
from services.jwt_service import require_active_user
from services.profile_service import ProfileService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/users#admin'


class GetUser(BaseController):
    """Detalle de un user por user_id (action `get-user`)."""

    event_model = AdminGetUserIn

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
        """Retorna 200 con el detalle, o 404 si el user no existe."""
        data: AdminGetUserIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        actor = require_active_user(meta.authorization, app_config=app_config)
        require_admin_user(
            actor, ip=meta.ip, user_agent=meta.user_agent,
            audit_action='admin.get-user',
        )

        detail = ProfileService(app_config).admin_detail(
            user_id=str(data.user_id),
        )
        if detail is None:
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'NOT_FOUND'},
            }
        return {'is_valid': True, 'code': 0, 'data': detail}
