"""Controller `mfa.delete` — borra (hard-delete) un metodo MFA del user.

Requiere access JWT valido. A diferencia de `mfa.disable` (soft-disable
reversible que conserva el row), ELIMINA el row de `auth_mfa_methods`: el
metodo vuelve a `configured:false` en el overview y un `setup-totp`
posterior empieza de cero. Pensado para que el boton 'Eliminar' de un
TOTP pendiente (setup abandonado) lo quite de verdad, no solo lo apague.

404 NOT_FOUND si el metodo no existe para el user (anti-enumeration).
409 MUST_KEEP_ONE_MFA_METHOD si borrar un metodo CONFIRMADO dejaria la
cuenta transversal en <= 1 (mismo invariante que `disable`/
`webauthn.delete-credential`). Un metodo NO confirmado (pendiente) NO
protege el invariante, asi que siempre se puede borrar (anti-lockout).
"""

from __future__ import annotations

from typing import Any

from models.mfa import MfaDeleteIn
from services.audit_service import AuditService
from services.auth_service import require_active_user
from services.mfa_method_service import MfaMethodService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.db.models.auth.enums import AuthMfaKind
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#mfa.delete'


class Delete(BaseController):
    """Borra un metodo MFA del user (action `delete`)."""

    event_model = MfaDeleteIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: MfaDeleteIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '',
            endpoint=_ENDPOINT,
            country=meta.country,
            turnstile_validated=True,
        )
        return base

    def execute(self) -> dict[str, Any]:
        """Borra el metodo si no deja al user sin MFA confirmado.

        Returns:
            404 NOT_FOUND si el metodo no existe para el user.
            409 MUST_KEEP_ONE_MFA_METHOD si borrar un metodo CONFIRMADO
            dejaria la cuenta transversal <= 1.
            204 si el metodo se borra.
        """
        data: MfaDeleteIn = self.validated_data  # type: ignore[assignment]
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

        # El guard MUST_KEEP_ONE solo protege metodos CONFIRMADOS: un metodo
        # no confirmado (ej. un setup-totp abandonado) no es una via de
        # entrada real, asi que siempre se puede borrar (anti-lockout).
        confirmed = mfa_svc.is_confirmed(user_id=user.id, kind=kind)
        if confirmed and mfa_svc.count_active(user_id=user.id) <= 1:
            return {
                'is_valid': False,
                'code': 4000,
                'status': 409,
                'data': {'error': 'MUST_KEEP_ONE_MFA_METHOD'},
            }

        mfa_svc.delete(user_id=user.id, kind=kind)

        audit_svc.log(
            event='mfa.delete',
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
