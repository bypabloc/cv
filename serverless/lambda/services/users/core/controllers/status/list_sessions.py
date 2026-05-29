"""Controller `status.list-sessions` — lista las sesiones activas (AC-8).

Requiere access JWT. Devuelve las sesiones del user ordenadas por
last_active_at DESC, marcando `current: true` la sesion cuyo family_id
coincide con el del access JWT en curso.
"""

from __future__ import annotations

from typing import Any

from models.status import StatusListSessionsIn
from services.jwt_service import authenticate
from services.rate_limit_service import RateLimitService
from services.session_service import SessionService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/users#status'


class ListSessions(BaseController):
    """Lista las sesiones activas del user (action `list-sessions`)."""

    event_model = StatusListSessionsIn

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
        """Retorna 200 con las sesiones activas (current marcado)."""
        data: StatusListSessionsIn = self.validated_data  # type: ignore[assignment]
        user, claims = authenticate(
            data.meta.authorization, app_config=app_config,
        )
        current_family = (
            str(claims.family_id) if claims.family_id is not None else None
        )
        sessions = SessionService(app_config).list_for_user(
            user_id=user.id, current_family_id=current_family,
        )
        return {
            'is_valid': True,
            'code': 0,
            'data': {'sessions': sessions},
        }
