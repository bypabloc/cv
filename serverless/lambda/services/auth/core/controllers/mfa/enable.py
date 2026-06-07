"""Controller `mfa.enable` — re-activa un metodo MFA soft-disabled.

Requiere access JWT valido. 404 NOT_FOUND si el metodo no existe para
el user (anti-enumeration). 204 si el metodo se re-activa.
"""

from __future__ import annotations

from typing import Any

from models.mfa import MfaEnableIn
from services.audit_service import AuditService
from services.auth_service import require_active_user
from services.mfa_method_service import MfaMethodService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.db.models.auth.enums import AuthMfaKind
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#mfa.enable'


class Enable(BaseController):
    """Re-activa un metodo MFA soft-disabled del user (action `enable`)."""

    event_model = MfaEnableIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: MfaEnableIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '',
            endpoint=_ENDPOINT,
            country=meta.country,
            turnstile_validated=True,
        )
        return base

    def execute(self) -> dict[str, Any]:
        """Re-activa el metodo MFA.

        Returns:
            404 NOT_FOUND si el metodo no existe para el user.
            204 si el metodo se re-activa.
        """
        data: MfaEnableIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)

        mfa_svc = MfaMethodService(app_config)
        audit_svc = AuditService(app_config)

        kind = AuthMfaKind(data.kind)
        ok = mfa_svc.enable(user_id=user.id, kind=kind)
        if not ok:
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'NOT_FOUND'},
            }

        audit_svc.log(
            event='mfa.enable',
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
