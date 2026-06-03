"""Controller `webauthn.enable` — reactiva un passkey desactivado.

Requiere access JWT valido. Toggle-on idempotente: revierte el
`disabled_at` del credential. 404 NOT_FOUND si el credential no existe
/ es de otro user (anti-enumeration).

AC cubiertos: AC-17, AC-25.
"""

from __future__ import annotations

from typing import Any

from models.webauthn import WebauthnEnableIn
from services.audit_service import AuditService
from services.auth_service import require_active_user
from services.rate_limit_service import RateLimitService
from services.webauthn_service import WebauthnService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#webauthn.enable'


class Enable(BaseController):
    """Reactiva un passkey desactivado (action `enable`)."""

    event_model = WebauthnEnableIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: WebauthnEnableIn = (
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
        """Revierte el `disabled_at` del credential.

        Returns:
            204 si el credential se reactiva.
            404 NOT_FOUND si el credential no existe / es de otro user.
        """
        data: WebauthnEnableIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)

        webauthn_svc = WebauthnService(app_config)
        audit_svc = AuditService(app_config)

        ok = webauthn_svc.enable(
            user_id=user.id,
            record_id=str(data.credential_id),
        )
        if not ok:
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'NOT_FOUND'},
            }

        audit_svc.log(
            event='webauthn.enable',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        return {
            'is_valid': True,
            'code': 0,
            'status': 204,
            'data': {},
        }
