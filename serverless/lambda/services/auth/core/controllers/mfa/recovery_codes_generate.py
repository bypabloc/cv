"""Controller `mfa.recovery-codes-generate` — emite 10 recovery codes.

Requiere access JWT valido. SIEMPRE regenera (borra los viejos del user
+ inserta 10 nuevos hashes). Devuelve los 10 codes en claro UNA vez;
NUNCA se loggea ni se vuelve a mostrar.

AC cubiertos: AC-7, AC-8.
"""

from __future__ import annotations

from typing import Any

from models.mfa import MfaRecoveryCodesGenerateIn
from services.audit_service import AuditService
from services.auth_service import require_active_user
from services.rate_limit_service import RateLimitService
from services.recovery_codes_service import RecoveryCodesService
from settings.config import app_config
from shared.lambda_kit import BaseController

_ENDPOINT = '/auth#mfa.recovery-codes-generate'


class RecoveryCodesGenerate(BaseController):
    """Emite 10 recovery codes nuevos (action `recovery-codes-generate`)."""

    event_model = MfaRecoveryCodesGenerateIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: MfaRecoveryCodesGenerateIn = (
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
        """Regenera y devuelve 10 recovery codes (mostrar UNA vez).

        Returns:
            200 `{codes: [...]}` con los 10 codes en claro.
        """
        data: MfaRecoveryCodesGenerateIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)

        recovery_svc = RecoveryCodesService(app_config)
        audit_svc = AuditService(app_config)

        codes = recovery_svc.generate(user_id=user.id)

        audit_svc.log(
            event='mfa.recovery-codes.regenerated',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        return {
            'is_valid': True,
            'code': 0,
            'data': {'codes': codes},
        }
