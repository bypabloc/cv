"""Controller `login.verify-magic-link` — link como factor de la lista.

El magic-link (GET del email) satisface el factor "code al email"
(`passwordless` o `email_code`) y delega en `decide_mfa_step`
(plan login-mfa-list-redesign):

- Si NO quedan factores required pendientes (alta / active sin otros
  required) -> emite access+refresh y redirige al callback con los tokens en
  el fragment (comportamiento actual, AC-15).
- Si quedan factores pendientes (active con required adicional) -> NO emite
  tokens: redirige al callback con un `temp_token` step=2 + los `methods`
  pendientes en el fragment, y el front continua el checklist (AC-14).

Marca `active` al user pending (cierra el alta) y `last_login_at`.

AC cubiertos: AC-14, AC-15.
"""

from __future__ import annotations

from typing import Any

from models.login import LoginVerifyMagicLinkIn
from services.audit_service import AuditService
from services.jwt_service import JwtService
from services.magic_link_service import MagicLinkService
from services.mfa_method_service import MfaMethodService
from services.rate_limit_service import RateLimitService
from services.user_service import UserService
from settings.config import app_config
from shared.db.models.auth.enums import AuthUserStatus
from shared.lambda_kit.base_controller import BaseController

from ._mfa_login import decide_mfa_step
from .verify_code import _email_factor

_ENDPOINT = '/auth#login.verify-magic-link'


class VerifyMagicLink(BaseController):
    """Verifica el magic-link de login (action `verify-magic-link`)."""

    event_model = LoginVerifyMagicLinkIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: LoginVerifyMagicLinkIn = (
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
        """Consume el link + emite access/refresh + update last_login."""
        data: LoginVerifyMagicLinkIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        link_svc = MagicLinkService(app_config)
        user_svc = UserService(app_config)
        jwt_svc = JwtService(app_config)
        mfa_svc = MfaMethodService(app_config)
        audit_svc = AuditService(app_config)

        consumed = link_svc.verify(plain=data.token)
        if consumed is None:
            state = link_svc.get_state(plain=data.token)
            if state is not None and state.consumed_at is not None:
                audit_svc.log(
                    event='login.verify-magic-link',
                    success=False,
                    error_code='LINK_CONSUMED',
                    ip=meta.ip,
                )
                return {
                    'is_valid': False,
                    'code': 4006,
                    'status': 400,
                    'data': {'error': 'LINK_CONSUMED'},
                }
            audit_svc.log(
                event='login.verify-magic-link',
                success=False,
                error_code='LINK_EXPIRED',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4007,
                'status': 400,
                'data': {'error': 'LINK_EXPIRED'},
            }

        user = user_svc.get_by_id(str(consumed.user_id))
        if user is None:
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'EMAIL_NOT_FOUND'},
            }

        # Fusion register -> login (bloque D): un user nuevo (pending) cierra
        # su registro al consumir el magic-link -> se marca active. Si ya esta
        # active, solo loguea.
        if user.status == AuthUserStatus.PENDING:
            user_svc.mark_active(user)

        # El link satisface el factor "code al email"; decide_mfa_step ve si
        # quedan factores required pendientes (satisfied arranca solo con el
        # factor email, sin estado previo: el GET del link no porta el temp del
        # checklist).
        required = mfa_svc.required_methods(user_id=user.id)
        factor = _email_factor(required)
        result = decide_mfa_step(
            jwt_svc=jwt_svc,
            app_config=app_config,
            user_id=user.id,
            satisfied=[factor],
            required=required,
            ip=meta.ip,
            country=meta.country,
            user_agent=meta.user_agent,
        )

        audit_svc.log(
            event='login.verify-magic-link',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        if result.get('mfa_complete'):
            # Login completo: redirige al callback con los tokens en el
            # fragment (comportamiento actual).
            user_svc.update_last_login(user)
            redirect_url = (
                f'{app_config.dashboard_callback_url}'
                f'#access={result["access_token"]}'
                f'&refresh={result["refresh_token"]}'
                f'&user_id={user.id}'
                f'&email={user.email}'
            )
            return {
                'is_valid': True,
                'code': 0,
                'data': {
                    'redirect_url': redirect_url,
                    **result,
                    'expires_in': 900,
                    'token_type': 'Bearer',
                    'user': {
                        'id': str(user.id),
                        'email': user.email,
                        'status': user.status.value,
                    },
                },
            }

        # Faltan factores: redirige al callback con el temp step=2 + los
        # methods pendientes; el front continua el checklist (sin tokens aun).
        redirect_url = (
            f'{app_config.dashboard_callback_url}'
            f'#temp={result["temp_token"]}'
            f'&methods={",".join(result["methods"])}'
            f'&step=2'
        )
        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'redirect_url': redirect_url,
                **result,
            },
        }
