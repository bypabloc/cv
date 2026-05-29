"""Controller `mfa.setup-email-code` — activa email-code como metodo MFA.

Requiere access JWT valido. El user ya probo recibir email en register,
asi que el metodo se inserta confirmado. Side-effect AC-27 si es el
primer MFA (lo gestiona el service).

AC cubiertos: parte del catalogo de metodos MFA.
"""

from __future__ import annotations

from typing import Any

from models.mfa import MfaSetupEmailCodeIn
from services.audit_service import AuditService
from services.auth_service import require_active_user
from services.mfa_method_service import MfaMethodService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#mfa.setup-email-code'


class SetupEmailCode(BaseController):
    """Activa email-code como metodo MFA (action `setup-email-code`)."""

    event_model = MfaSetupEmailCodeIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: MfaSetupEmailCodeIn = (
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
        """Activa el metodo email-code (confirmado de inmediato).

        Returns:
            204 al activar el metodo.
        """
        data: MfaSetupEmailCodeIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)

        mfa_svc = MfaMethodService(app_config)
        audit_svc = AuditService(app_config)

        mfa_svc.setup_email_code(user_id=user.id)

        audit_svc.log(
            event='mfa.setup-email-code',
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
