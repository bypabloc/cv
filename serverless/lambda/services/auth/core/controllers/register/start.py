"""Controller `register.start` — inicia el flujo de registro.

Orquestador del primer paso del flujo de registro. Verifica Turnstile,
rate-limit per-IP, idempotencia (email existente), crea/upserta el user
en `pending`, genera code de 8 chars + magic-link opaco, publica 2
mensajes SQS al `auth_email_worker` y devuelve un temp_token (rolling
JWT, 5 min) para continuar al paso siguiente.

AC cubiertos: AC-1, AC-2, AC-12, AC-13, AC-19, AC-20.
"""

from __future__ import annotations

from typing import Any

from models.register import RegisterStartIn
from services.audit_service import AuditService
from services.code_service import CODE_TTL_MINUTES, CodeService
from services.email_dispatch_service import EmailDispatchService
from services.jwt_service import JwtService
from services.magic_link_service import LINK_TTL_MINUTES, MagicLinkService
from services.rate_limit_service import RateLimitService
from services.user_service import UserService
from settings.config import app_config
from shared.crypto.captcha import verify_captcha_or_bypass
from shared.db.models.auth.enums import (
    AuthCodeKind,
    AuthLinkKind,
    AuthUserStatus,
)
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#register.start'
_TEMP_TTL_SECONDS = 300


class Start(BaseController):
    """Inicia el flujo de registro (action `start`).

    Flujo:
      1. validate(): rate-limit + Turnstile.
      2. execute(): idempotencia + genera artefactos + publica emails.
    """

    event_model = RegisterStartIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit + Turnstile.

        El rate-limit puede levantar `RateLimitExceededError` (HTTP 429)
        o `IPBlacklistedError`/`CountryBlockedError` (HTTP 403). El
        Turnstile puede levantar `TurnstileError` (HTTP 403). Ambas
        excepciones las traduce `http_handler` al status correcto.
        """
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: RegisterStartIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta

        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '',
            endpoint=_ENDPOINT,
            country=meta.country,
            turnstile_validated=False,
        )

        verify_captcha_or_bypass(
            data.cf_turnstile_response,
            remote_ip=meta.ip,
            bypass_token=meta.bypass_token,
        )

        return base

    def execute(self) -> dict[str, Any]:
        """Idempotencia + genera artefactos + publica emails.

        Returns:
            En exito: `{is_valid: True, code: 0, data: {temp_token,
            user_id, expires_in}}` (HTTP 200).
            Email already registered: `{is_valid: False, code: 4002,
            data: {error}, status: 409}`.
            Email disabled/locked: `{is_valid: False, code: 4001, data:
            {error, suggest_register: False}, status: 404}` (anti-
            enumeration, AC-20).
        """
        data: RegisterStartIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        email = data.email.lower()
        niche = data.niche

        user_svc = UserService(app_config)
        code_svc = CodeService(app_config)
        link_svc = MagicLinkService(app_config)
        jwt_svc = JwtService(app_config)
        email_svc = EmailDispatchService(app_config)
        audit_svc = AuditService(app_config)

        existing = user_svc.get_by_email(email)

        if existing is not None:
            if existing.status == AuthUserStatus.ACTIVE:
                audit_svc.log(
                    event='register.start',
                    success=False,
                    user_id=existing.id,
                    error_code='EMAIL_ALREADY_REGISTERED',
                    ip=meta.ip,
                    user_agent=meta.user_agent,
                    niche=niche,
                )
                return {
                    'is_valid': False,
                    'code': 4002,
                    'data': {'error': 'EMAIL_ALREADY_REGISTERED'},
                    'status': 409,
                }
            if existing.status in (
                AuthUserStatus.DISABLED,
                AuthUserStatus.LOCKED,
            ):
                audit_svc.log(
                    event='register.start',
                    success=False,
                    user_id=existing.id,
                    error_code='EMAIL_NOT_FOUND',
                    ip=meta.ip,
                    user_agent=meta.user_agent,
                    niche=niche,
                )
                return {
                    'is_valid': False,
                    'code': 4001,
                    'data': {
                        'error': 'EMAIL_NOT_FOUND',
                        'suggest_register': False,
                    },
                    'status': 404,
                }
            # status pending: invalidar codes + links previos (AC-19),
            # reutiliza el mismo user.
            user_svc.invalidate_active_codes_and_links(
                user_id=str(existing.id),
                kind_code=AuthCodeKind.REGISTER,
                kind_link=AuthLinkKind.REGISTER,
            )
            user = existing
        else:
            user = user_svc.create_pending(email=email)

        code, _ = code_svc.generate_and_persist(
            user_id=user.id,
            kind=AuthCodeKind.REGISTER,
        )
        token, _ = link_svc.generate_and_persist(
            user_id=user.id,
            kind=AuthLinkKind.REGISTER,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        verify_url = (
            f'{app_config.magic_link_base_url}'
            f'?operation=register&action=verify-magic-link&token={token}'
        )
        email_svc.publish_magic_link(
            to=user.email,
            user_id=user.id,
            niche=niche,
            kind='register-magic-link',
            verify_url=verify_url,
            expires_in_min=LINK_TTL_MINUTES,
        )
        email_svc.publish_code(
            to=user.email,
            user_id=user.id,
            niche=niche,
            kind='register-code',
            code=code,
            expires_in_min=CODE_TTL_MINUTES,
        )

        temp_token, _ = jwt_svc.issue_temp(
            user_id=user.id,
            flow='register',
            step=1,
        )

        audit_svc.log(
            event='register.start',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
            niche=niche,
        )

        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'temp_token': temp_token,
                'user_id': str(user.id),
                'expires_in': _TEMP_TTL_SECONDS,
            },
        }
