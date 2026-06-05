"""Controller `security.password-set-required` — flag required de la password.

Marca/desmarca la password como factor exigido al loguear (modelo de lista).
Requiere access JWT. 404 NOT_FOUND si el user no tiene password.

El invariante "siempre >=1 required" lo garantiza el sistema, NO un 409:
`required_methods` antepone `passwordless` como fallback cuando el user no
tiene ningun otro factor explicito (decision del usuario: "passwordless es
required cuando esta solo"). Por eso desmarcar la password SIEMPRE es seguro
— el user queda con sus otros factores required o, en el peor caso, con
passwordless (code/magic-link al email). No hay forma de quedar sin login.

AC cubiertos: AC-7, AC-8.
"""

from __future__ import annotations

from typing import Any

from models.security import SecurityPasswordSetRequiredIn
from services.audit_service import AuditService
from services.auth_service import require_active_user
from services.password_service import PasswordService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#security.password-set-required'


class PasswordSetRequired(BaseController):
    """Marca/desmarca la password como required (action `password-set-required`)."""

    event_model = SecurityPasswordSetRequiredIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: SecurityPasswordSetRequiredIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '',
            endpoint=_ENDPOINT,
            country=meta.country,
            turnstile_validated=True,
        )
        return base

    def execute(self) -> dict[str, Any]:
        """Actualiza `auth_credentials.required`.

        Returns:
            404 NOT_FOUND si el user no tiene password.
            204 si el flag se actualiza.
        """
        data: SecurityPasswordSetRequiredIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)
        audit_svc = AuditService(app_config)

        ok = PasswordService(app_config).set_required(
            user_id=user.id,
            required=data.required,
        )
        if not ok:
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'NOT_FOUND'},
            }

        audit_svc.log(
            event='security.password-set-required',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )
        return {'is_valid': True, 'code': 0, 'status': 204, 'data': {}}
