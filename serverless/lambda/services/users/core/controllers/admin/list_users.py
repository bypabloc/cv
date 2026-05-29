"""Controller `admin.list-users` — listado paginado de users (AC-11/12/13).

Requiere access JWT + admin. NO-admin -> 404 NOT_FOUND (anti-enumeration).
Paginacion cursor-based por uuidv7 id ASC.
"""

from __future__ import annotations

from typing import Any

from models.admin import AdminListUsersIn
from services.admin_service import require_admin_user
from services.jwt_service import require_active_user
from services.profile_service import ProfileService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.lambda_kit import BaseController

_ENDPOINT = '/users#admin'


class ListUsers(BaseController):
    """Lista users paginado (action `list-users`)."""

    event_model = AdminListUsersIn

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
        """Retorna 200 con la pagina de users + next_cursor."""
        data: AdminListUsersIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        actor = require_active_user(meta.authorization, app_config=app_config)
        require_admin_user(
            actor, ip=meta.ip, user_agent=meta.user_agent,
            audit_action='admin.list-users',
        )

        cursor = str(data.cursor) if data.cursor is not None else None
        users = ProfileService(app_config).list_paginated(
            cursor=cursor,
            page_size=data.page_size,
            status_filter=data.status_filter,
        )
        items = [
            {
                'id': str(user.id),
                'email': user.email,
                'status': user.status.value,
                'created_at': user.created_at.isoformat(),
                'display_name': user.display_name,
            }
            for user in users
        ]
        next_cursor = (
            items[-1]['id'] if len(items) == data.page_size else None
        )
        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'users': items,
                'next_cursor': next_cursor,
                'page_size': data.page_size,
                'total_returned': len(items),
            },
        }
