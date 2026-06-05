"""Controller `security.overview` — estado unificado de seguridad del user.

Requiere access JWT valido. Devuelve SIEMPRE 5 entradas con shape
uniforme (`type/label/configured/enabled/required/preferred/created_at/
last_used_at/detail`): totp, email_code, webauthn, recovery_codes y
password. Cada entrada reporta si esta configurada y habilitada, asi el
frontend renderiza la pantalla de seguridad con una sola llamada.

Sin Turnstile (endpoint JWT-authed). Rate-limit per-IP con el limite
alto (`turnstile_validated=True`).
"""

from __future__ import annotations

from typing import Any

from models.security import SecurityOverviewIn
from services.auth_service import require_active_user
from services.mfa_method_service import MfaMethodService
from services.password_service import PasswordService
from services.rate_limit_service import RateLimitService
from services.recovery_codes_service import RecoveryCodesService
from services.webauthn_service import WebauthnService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#security.overview'

# Etiquetas legibles (es) por tipo de metodo.
_LABELS = {
    'totp': 'App de autenticacion (TOTP)',
    'email_code': 'Codigo por email',
    'webauthn': 'Llaves de acceso (passkeys)',
    'recovery_codes': 'Codigos de recuperacion',
    'password': 'Contrasena',
}


def _mfa_entry(method_type: str, method: dict[str, Any] | None) -> dict[str, Any]:
    """Construye la entrada de un metodo MFA (totp / email_code).

    `method` es el dict de `MfaMethodService.list_all` o None si el user
    no tiene ese metodo configurado.
    """
    if method is None:
        return {
            'type': method_type,
            'label': _LABELS[method_type],
            'configured': False,
            'enabled': False,
            'required': False,
            'preferred': False,
            'created_at': None,
            'last_used_at': None,
            'detail': {},
        }
    return {
        'type': method_type,
        'label': _LABELS[method_type],
        'configured': True,
        'enabled': bool(method['enabled']),
        'required': bool(method['required']),
        'preferred': bool(method['preferred']),
        'created_at': method['created_at'],
        'last_used_at': method['last_used_at'],
        'detail': {'confirmed': bool(method['confirmed'])},
    }


class Overview(BaseController):
    """Estado unificado de seguridad del user (action `overview`)."""

    event_model = SecurityOverviewIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: SecurityOverviewIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '',
            endpoint=_ENDPOINT,
            country=meta.country,
            turnstile_validated=True,
        )
        return base

    def execute(self) -> dict[str, Any]:
        """Arma SIEMPRE las 5 entradas de seguridad del user.

        Returns:
            200 `{methods: [totp, email_code, webauthn, recovery_codes,
            password]}` con shape uniforme por entrada.
        """
        data: SecurityOverviewIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)

        mfa_svc = MfaMethodService(app_config)
        webauthn_svc = WebauthnService(app_config)
        recovery_svc = RecoveryCodesService(app_config)
        password_svc = PasswordService(app_config)

        # --- MFA methods (totp + email_code) ---
        mfa_by_kind = {
            method['kind']: method
            for method in mfa_svc.list_all(user_id=user.id)
        }
        totp_entry = _mfa_entry('totp', mfa_by_kind.get('totp'))
        email_code_entry = _mfa_entry(
            'email_code',
            mfa_by_kind.get('email_code'),
        )

        # --- WebAuthn (passkeys) ---
        credentials = webauthn_svc.list_all(user_id=user.id)
        webauthn_entry = {
            'type': 'webauthn',
            'label': _LABELS['webauthn'],
            'configured': len(credentials) > 0,
            'enabled': any(cred['enabled'] for cred in credentials),
            'required': any(cred['required'] for cred in credentials),
            'preferred': False,
            'created_at': None,
            'last_used_at': None,
            'detail': {'credentials': credentials},
        }

        # --- Recovery codes ---
        recovery_counts = recovery_svc.counts(user_id=user.id)
        recovery_entry = {
            'type': 'recovery_codes',
            'label': _LABELS['recovery_codes'],
            'configured': recovery_counts['total'] > 0,
            'enabled': recovery_counts['remaining'] > 0,
            'required': False,
            'preferred': False,
            'created_at': None,
            'last_used_at': None,
            'detail': {
                'total': recovery_counts['total'],
                'remaining': recovery_counts['remaining'],
            },
        }

        # --- Password ---
        password_status = password_svc.status(user_id=user.id)
        has_password = bool(password_status['has_password'])
        password_entry = {
            'type': 'password',
            'label': _LABELS['password'],
            'configured': has_password,
            'enabled': has_password,
            'required': bool(password_status['required']),
            'preferred': False,
            'created_at': None,
            'last_used_at': None,
            'detail': {'last_change_at': password_status['last_change_at']},
        }

        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'methods': [
                    totp_entry,
                    email_code_entry,
                    webauthn_entry,
                    recovery_entry,
                    password_entry,
                ],
            },
        }
