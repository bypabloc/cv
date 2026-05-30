"""Controller `mfa.set-preferred` — cambia el metodo MFA preferido.

Requiere access JWT valido. Marca `kind` como preferido (unset en los
demas). 400 MFA_NOT_CONFIGURED si el user no tiene ese metodo activo.

AC cubiertos: AC-4.
"""

from __future__ import annotations

from typing import Any

from models.mfa import MfaSetPreferredIn
from services.audit_service import AuditService
from services.auth_service import require_active_user
from services.mfa_method_service import MfaMethodService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.db.models.auth.enums import AuthMfaKind
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#mfa.set-preferred'


class SetPreferred(BaseController):
    """Cambia el metodo MFA preferido (action `set-preferred`)."""

    event_model = MfaSetPreferredIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: MfaSetPreferredIn = (
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
        """Marca `kind` como preferido.

        Returns:
            204 si el metodo existe y se marca como preferido.
            400 MFA_NOT_CONFIGURED si el user no tiene ese metodo activo.
        """
        data: MfaSetPreferredIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)

        mfa_svc = MfaMethodService(app_config)
        audit_svc = AuditService(app_config)

        kind = AuthMfaKind(data.kind)
        ok = mfa_svc.set_preferred(user_id=user.id, kind=kind)
        if not ok:
            return {
                'is_valid': False,
                'code': 4000,
                'status': 400,
                'data': {'error': 'MFA_NOT_CONFIGURED'},
            }

        audit_svc.log(
            event='mfa.set-preferred',
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
