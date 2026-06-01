"""Controller `mfa.setup-totp` — genera el secret TOTP + otpauth_url.

Requiere access JWT valido (header Authorization). Genera un secret
base32, lo cifra con KMS (CMK directa, EncryptionContext del user) y lo
persiste como metodo TOTP pendiente (confirmed_at=NULL). Devuelve el
secret en claro UNA vez + la otpauth_url para que el frontend renderice
el QR. NUNCA loggea el secret.

AC cubiertos: AC-1.
"""

from __future__ import annotations

from typing import Any

from models.mfa import MfaSetupTotpIn
from services.audit_service import AuditService
from services.auth_service import require_active_user
from services.mfa_method_service import MfaMethodService
from services.rate_limit_service import RateLimitService
from services.totp_service import TotpService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#mfa.setup-totp'


class SetupTotp(BaseController):
    """Genera el secret TOTP del user (action `setup-totp`)."""

    event_model = MfaSetupTotpIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: MfaSetupTotpIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '',
            endpoint=_ENDPOINT,
            country=meta.country,
            turnstile_validated=True,
        )
        return base

    def execute(self) -> dict[str, Any]:
        """Cifra y persiste el secret pendiente; devuelve secret + otpauth.

        Returns:
            200 `{secret_b32, otpauth_url}` (mostrar UNA vez).
        """
        data: MfaSetupTotpIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)

        totp_svc = TotpService(app_config)
        mfa_svc = MfaMethodService(app_config)
        audit_svc = AuditService(app_config)

        secret_b32 = totp_svc.generate_secret()
        ciphertext = totp_svc.encrypt_secret(
            secret_b32=secret_b32,
            user_id=user.id,
        )
        mfa_svc.upsert_pending_totp(user_id=user.id, ciphertext=ciphertext)
        otpauth_url = totp_svc.otpauth_url(
            secret_b32=secret_b32,
            email=user.email,
        )

        audit_svc.log(
            event='mfa.setup-totp',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'secret_b32': secret_b32,
                'otpauth_url': otpauth_url,
            },
        }
