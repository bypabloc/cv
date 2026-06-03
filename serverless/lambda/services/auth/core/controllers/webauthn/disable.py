"""Controller `webauthn.disable` — desactiva un passkey (reversible).

Requiere access JWT valido. Toggle-off reversible: marca el credential
`disabled_at` (no lo borra). 409 MUST_KEEP_ONE_MFA_METHOD si desactivar
el credential dejaria al user con `total_mfa == 0` (cuenta transversal,
AC-17). 404 NOT_FOUND si el credential no existe / es de otro user
(AC-25, anti-enumeration).

AC cubiertos: AC-17, AC-25.
"""

from __future__ import annotations

from typing import Any

from models.webauthn import WebauthnDisableIn
from services.audit_service import AuditService
from services.auth_service import require_active_user
from services.rate_limit_service import RateLimitService
from services.webauthn_service import WebauthnService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#webauthn.disable'


class Disable(BaseController):
    """Desactiva un passkey reversible (action `disable`)."""

    event_model = WebauthnDisableIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: WebauthnDisableIn = (
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
        """Marca el `disabled_at` del credential si no deja al user sin MFA.

        Returns:
            409 MUST_KEEP_ONE_MFA_METHOD si la cuenta transversal <= 1
            (AC-17).
            404 NOT_FOUND si el credential no existe / es de otro user
            (AC-25).
            204 si el credential se desactiva.
        """
        data: WebauthnDisableIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)

        webauthn_svc = WebauthnService(app_config)
        audit_svc = AuditService(app_config)

        if webauthn_svc.count_active(user_id=user.id) <= 1:
            return {
                'is_valid': False,
                'code': 4000,
                'status': 409,
                'data': {'error': 'MUST_KEEP_ONE_MFA_METHOD'},
            }

        ok = webauthn_svc.soft_disable(
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
            event='webauthn.disable',
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
