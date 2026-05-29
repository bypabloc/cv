"""Controller `mfa.confirm-totp` — verifica el primer code y activa el TOTP.

Requiere access JWT valido. Lee el ciphertext del row TOTP pendiente,
descifra + verifica el code de 6 digitos. Si OK, confirma el metodo
(side-effect AC-27: si es el primer MFA, revoca las sesiones del user).

AC cubiertos: AC-2, AC-3.
"""

from __future__ import annotations

from typing import Any

from models.mfa import MfaConfirmTotpIn
from services.audit_service import AuditService
from services.auth_service import require_active_user
from services.mfa_method_service import MfaMethodService
from services.rate_limit_service import RateLimitService
from services.totp_service import TotpService
from settings.config import app_config
from shared.db.models import AuthMfaKind
from shared.lambda_kit import BaseController

_ENDPOINT = '/auth#mfa.confirm-totp'


class ConfirmTotp(BaseController):
    """Confirma el metodo TOTP del user (action `confirm-totp`)."""

    event_model = MfaConfirmTotpIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: MfaConfirmTotpIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '',
            endpoint=_ENDPOINT,
            country=meta.country,
            turnstile_validated=True,
        )
        return base

    def execute(self) -> dict[str, Any]:
        """Verifica el code y confirma el metodo.

        Returns:
            204 si el code es correcto (metodo confirmado).
            404 NO_PENDING_TOTP si no hay row TOTP pendiente.
            400 INVALID_TOTP_CODE si el code no matchea.
        """
        data: MfaConfirmTotpIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)

        totp_svc = TotpService(app_config)
        mfa_svc = MfaMethodService(app_config)
        audit_svc = AuditService(app_config)

        ciphertext = mfa_svc.get_totp_ciphertext(
            user_id=user.id,
            require_confirmed=False,
        )
        if ciphertext is None:
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'NO_PENDING_TOTP'},
            }

        ok = totp_svc.verify(
            user_id=user.id,
            ciphertext=ciphertext,
            code=data.code,
        )
        if not ok:
            audit_svc.log(
                event='mfa.confirm-totp',
                success=False,
                user_id=user.id,
                error_code='INVALID_TOTP_CODE',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 1002,
                'status': 400,
                'data': {'error': 'INVALID_TOTP_CODE'},
            }

        mfa_svc.confirm(user_id=user.id, kind=AuthMfaKind.TOTP)

        audit_svc.log(
            event='mfa.confirm-totp',
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
