"""Controller `webauthn.list-credentials` — lista los passkeys del user.

Requiere access JWT valido. Devuelve los credentials activos ordenados
por last_used_at DESC (el service ya los ordena).

AC cubiertos: AC-16.
"""

from __future__ import annotations

from typing import Any

from models.webauthn import WebauthnListCredentialsIn
from services.auth_service import require_active_user
from services.webauthn_service import WebauthnService
from settings.config import app_config
from shared.lambda_kit import BaseController


class ListCredentials(BaseController):
    """Lista los passkeys del user (action `list-credentials`)."""

    event_model = WebauthnListCredentialsIn

    def execute(self) -> dict[str, Any]:
        """Devuelve los credentials activos del user.

        Returns:
            200 `{credentials: [{credential_id, nickname, ...}, ...]}`.
        """
        data: WebauthnListCredentialsIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)

        webauthn_svc = WebauthnService(app_config)
        credentials = webauthn_svc.list_credentials(user_id=user.id)

        return {
            'is_valid': True,
            'code': 0,
            'data': {'credentials': credentials},
        }
