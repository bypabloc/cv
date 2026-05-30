"""Controller `login.start` — inicia el flujo de login passwordless.

Espejo de `register.start`. El visitante existente pide login: el
controller verifica Turnstile + rate-limit, valida que el email exista
y este activo, genera code + magic-link nuevos, publica los 2 mensajes
SQS al worker, y devuelve un temp_token (rolling JWT, 5 min) con
flow='login'.

AC cubiertos: AC-5, AC-6, AC-20.
"""

from __future__ import annotations

from typing import Any

from models.login import LoginStartIn
from services.audit_service import AuditService
from services.code_service import CODE_TTL_MINUTES, CodeService
from services.email_dispatch_service import EmailDispatchService
from services.jwt_service import JwtService
from services.magic_link_service import LINK_TTL_MINUTES, MagicLinkService
from services.mfa_method_service import MfaMethodService
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

from ._mfa_login import issue_terminal_tokens
from ._password_check import check_password

_ENDPOINT = '/auth#login.start'
_TEMP_TTL_SECONDS = 300
# Factor fuerte: el temp JWT step=2 producido tras password lleva este
# flow (decision 10). Solo metodos fuertes post-password.
_MFA_FLOW = 'login-mfa'
_MFA_METHODS = ['totp', 'webauthn']


class Start(BaseController):
    """Inicia el flujo de login (action `start`)."""

    event_model = LoginStartIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit + Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: LoginStartIn = self.validated_data  # type: ignore[assignment]
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
        """Verifica que el email exista/active, publica code + magic-link.

        Returns:
            Exito: `{is_valid: True, code: 0, data: {temp_token,
            methods, expires_in}}` (HTTP 200).
            Email no existe: 404 EMAIL_NOT_FOUND con suggest_register=True
            (AC-5).
            Email pending: 409 PENDING_VERIFICATION.
            Email disabled/locked: 404 EMAIL_NOT_FOUND, suggest_register
            =False (AC-20, anti-enumeration).
        """
        data: LoginStartIn = self.validated_data  # type: ignore[assignment]
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

        if existing is None:
            audit_svc.log(
                event='login.start',
                success=False,
                error_code='EMAIL_NOT_FOUND',
                ip=meta.ip,
                user_agent=meta.user_agent,
                niche=niche,
            )
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {
                    'error': 'EMAIL_NOT_FOUND',
                    'suggest_register': True,
                    'methods': [],
                },
            }

        if existing.status == AuthUserStatus.PENDING:
            audit_svc.log(
                event='login.start',
                success=False,
                user_id=existing.id,
                error_code='PENDING_VERIFICATION',
                ip=meta.ip,
                niche=niche,
            )
            return {
                'is_valid': False,
                'code': 4011,
                'status': 409,
                'data': {'error': 'PENDING_VERIFICATION'},
            }

        if existing.status in (
            AuthUserStatus.DISABLED,
            AuthUserStatus.LOCKED,
        ):
            audit_svc.log(
                event='login.start',
                success=False,
                user_id=existing.id,
                error_code='EMAIL_NOT_FOUND',
                ip=meta.ip,
                niche=niche,
            )
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {
                    'error': 'EMAIL_NOT_FOUND',
                    'suggest_register': False,
                    'methods': [],
                },
            }

        # status active + password en el body (plan 02, decision 9): valida
        # con argon2 ANTES de la rama passwordless. NO toca el passwordless.
        if data.password is not None:
            return self._login_with_password(
                user=existing,
                password=data.password,
                niche=niche,
                meta=meta,
                user_svc=user_svc,
                jwt_svc=jwt_svc,
                audit_svc=audit_svc,
            )

        # status active: invalidar codes + links previos + generar nuevos.
        user_svc.invalidate_active_codes_and_links(
            user_id=str(existing.id),
            kind_code=AuthCodeKind.LOGIN,
            kind_link=AuthLinkKind.LOGIN,
        )

        code, _ = code_svc.generate_and_persist(
            user_id=existing.id,
            kind=AuthCodeKind.LOGIN,
        )
        token, _ = link_svc.generate_and_persist(
            user_id=existing.id,
            kind=AuthLinkKind.LOGIN,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        verify_url = (
            f'{app_config.magic_link_base_url}'
            f'?operation=login&action=verify-magic-link&token={token}'
        )
        email_svc.publish_magic_link(
            to=existing.email,
            user_id=existing.id,
            niche=niche,
            kind='login-magic-link',
            verify_url=verify_url,
            expires_in_min=LINK_TTL_MINUTES,
        )
        email_svc.publish_code(
            to=existing.email,
            user_id=existing.id,
            niche=niche,
            kind='login-code',
            code=code,
            expires_in_min=CODE_TTL_MINUTES,
        )

        temp_token, _ = jwt_svc.issue_temp(
            user_id=existing.id,
            flow='login',
            step=1,
        )

        audit_svc.log(
            event='login.start',
            success=True,
            user_id=existing.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
            niche=niche,
        )

        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'temp_token': temp_token,
                'methods': ['magic-link', 'email-code'],
                'expires_in': _TEMP_TTL_SECONDS,
            },
        }

    def _login_with_password(
        self,
        *,
        user: Any,
        password: str,
        niche: str | None,
        meta: Any,
        user_svc: Any,
        jwt_svc: Any,
        audit_svc: Any,
    ) -> dict[str, Any]:
        """Login con password directo (plan 02).

        Returns:
            401 INVALID_PASSWORD + failed_attempts++ si no matchea (AC-21).
            200 access+refresh si el user no tiene MFA (AC-20).
            200 temp step=2 + methods=['totp','webauthn'] si tiene MFA
            (AC-18).
        """
        if not check_password(user_id=user.id, password=password):
            user_svc.increment_failed_attempts(user)
            audit_svc.log(
                event='login.start',
                success=False,
                user_id=user.id,
                error_code='INVALID_PASSWORD',
                ip=meta.ip,
                niche=niche,
            )
            return {
                'is_valid': False,
                'code': 4000,
                'status': 401,
                'data': {'error': 'INVALID_PASSWORD'},
            }

        mfa_svc = MfaMethodService(app_config)
        if mfa_svc.count_active(user_id=user.id) == 0:
            tokens = issue_terminal_tokens(
                jwt_svc=jwt_svc,
                user_id=user.id,
                app_config=app_config,
                ip=meta.ip,
                country=meta.country,
                user_agent=meta.user_agent,
            )
            user_svc.update_last_login(user)
            audit_svc.log(
                event='login.start',
                success=True,
                user_id=user.id,
                ip=meta.ip,
                user_agent=meta.user_agent,
                niche=niche,
            )
            return {'is_valid': True, 'code': 0, 'data': tokens}

        temp_token, _ = jwt_svc.issue_temp(
            user_id=user.id,
            flow=_MFA_FLOW,
            step=2,
        )
        audit_svc.log(
            event='login.start',
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
                'methods': list(_MFA_METHODS),
                'step': 2,
            },
        }
