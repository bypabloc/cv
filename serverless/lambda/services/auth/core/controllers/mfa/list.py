"""Controller `mfa.list` — lista los metodos MFA activos del user.

Requiere access JWT valido. Devuelve los metodos activos como dicts
serializables (kind, preferred, confirmed).

AC cubiertos: catalogo de metodos MFA.
"""

from __future__ import annotations

from typing import Any

from models.mfa import MfaListIn
from services.auth_service import require_active_user
from services.mfa_method_service import MfaMethodService
from settings.config import app_config
from shared.lambda_kit import BaseController


class List(BaseController):
    """Lista los metodos MFA activos del user (action `list`)."""

    event_model = MfaListIn

    def execute(self) -> dict[str, Any]:
        """Devuelve los metodos activos del user.

        Returns:
            200 `{methods: [{kind, preferred, confirmed}, ...]}`.
        """
        data: MfaListIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)

        mfa_svc = MfaMethodService(app_config)
        methods = mfa_svc.list_active(user_id=user.id)

        return {
            'is_valid': True,
            'code': 0,
            'data': {'methods': methods},
        }
