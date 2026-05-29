"""Controller `mfa.disable` — deshabilita un metodo MFA (no si es el unico).

Requiere access JWT valido. 404 NOT_FOUND si el metodo no existe para
el user (AC-5b, anti-enumeration). 409 MUST_KEEP_ONE_MFA_METHOD si la
cuenta transversal de metodos activos es <= 1 (AC-5). Si hay >= 2,
deshabilita el metodo (AC-6).

AC cubiertos: AC-5, AC-5b, AC-6.
"""

from __future__ import annotations

from typing import Any

from models.mfa import MfaDisableIn
from services.audit_service import AuditService
from services.auth_service import require_active_user
from services.mfa_method_service import MfaMethodService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.db.models import AuthMfaKind
from shared.lambda_kit import BaseController

_ENDPOINT = '/auth#mfa.disable'


class Disable(BaseController):
    """Deshabilita un metodo MFA del user (action `disable`)."""

    event_model = MfaDisableIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: MfaDisableIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '',
            endpoint=_ENDPOINT,
            country=meta.country,
            turnstile_validated=True,
        )
        return base

    def execute(self) -> dict[str, Any]:
        """Deshabilita el metodo si no deja al user sin MFA.

        Returns:
            404 NOT_FOUND si el metodo no existe para el user (AC-5b).
            409 MUST_KEEP_ONE_MFA_METHOD si la cuenta transversal <= 1
            (AC-5).
            204 si el metodo se deshabilita (AC-6).
        """
        data: MfaDisableIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)

        mfa_svc = MfaMethodService(app_config)
        audit_svc = AuditService(app_config)

        kind = AuthMfaKind(data.kind)
        if not mfa_svc.has_active_method(user_id=user.id, kind=kind):
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'NOT_FOUND'},
            }

        if mfa_svc.count_active(user_id=user.id) <= 1:
            return {
                'is_valid': False,
                'code': 4000,
                'status': 409,
                'data': {'error': 'MUST_KEEP_ONE_MFA_METHOD'},
            }

        mfa_svc.disable(user_id=user.id, kind=kind)

        audit_svc.log(
            event='mfa.disable',
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
