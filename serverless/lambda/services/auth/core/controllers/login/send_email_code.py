"""Controller `login.send-email-code` — envia el code dentro del checklist.

Cuando el factor "code al email" (`passwordless` / `email_code`) es uno de los
metodos required del checklist, el front pide este endpoint al expandir ese
metodo: genera un code + magic-link nuevos y envia el email unificado, para
que el user pueda verificarlo con `login.verify-code` / el magic-link.

Reemplaza el envio que antes hacia `login.start` para el caso passwordless;
ahora `login.start` (user active) solo abre el checklist y el envio del code
se dispara on-demand (evita mandar un email a quien va a entrar con otro
factor).

Requiere un temp step=2 (`flow='login-mfa[:...]'`) del checklist.

AC cubiertos: AC-13.
"""

from __future__ import annotations

from typing import Any

from models.login import LoginSendEmailCodeIn
from services.audit_service import AuditService
from services.code_service import CodeService
from services.email_dispatch_service import EmailDispatchService
from services.jwt_service import JwtService
from services.magic_link_service import LINK_TTL_MINUTES, MagicLinkService
from services.rate_limit_service import RateLimitService
from services.user_service import UserService
from settings.config import app_config
from shared.auth.jwt import JwtError
from shared.db.models.auth.enums import AuthCodeKind, AuthLinkKind
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#login.send-email-code'
_MFA_FLOW = 'login-mfa'


class SendEmailCode(BaseController):
    """Envia el code del checklist (action `send-email-code`)."""

    event_model = LoginSendEmailCodeIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: LoginSendEmailCodeIn = (
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
        """Verifica el temp step=2, genera+envia el code+magic-link.

        Returns:
            401 TOKEN_INVALID si el temp no verifica o no es step=2 login-mfa.
            200 `{ok:true}` tras enviar el email unificado.
        """
        data: LoginSendEmailCodeIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        jwt_svc = JwtService(app_config)
        user_svc = UserService(app_config)
        audit_svc = AuditService(app_config)

        try:
            claims = jwt_svc.verify(data.temp_token, expected_typ='temp')
        except JwtError:
            return self._token_invalid(audit_svc=audit_svc, meta=meta)

        flow_ok = (
            claims.flow is not None
            and claims.flow.split(':', 1)[0] == _MFA_FLOW
        )
        if not flow_ok or claims.step != 2:
            return self._token_invalid(audit_svc=audit_svc, meta=meta)

        user = user_svc.get_by_id(str(claims.sub))
        if user is None:
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'EMAIL_NOT_FOUND'},
            }

        # NO blacklistea el temp: el checklist sigue abierto (el user
        # verificara el code con el MISMO temp step=2 via login.verify-code).
        user_svc.invalidate_active_codes_and_links(
            user_id=str(user.id),
            kind_code=AuthCodeKind.LOGIN,
            kind_link=AuthLinkKind.LOGIN,
        )
        code, _ = CodeService(app_config).generate_and_persist(
            user_id=user.id,
            kind=AuthCodeKind.LOGIN,
        )
        token, _ = MagicLinkService(app_config).generate_and_persist(
            user_id=user.id,
            kind=AuthLinkKind.LOGIN,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )
        verify_url = (
            f'{app_config.magic_link_base_url}'
            f'?operation=login&action=verify-magic-link&token={token}'
        )
        EmailDispatchService(app_config).publish_unified(
            to=user.email,
            user_id=user.id,
            niche=None,
            kind='login-unified',
            verify_url=verify_url,
            code=code,
            expires_in_min=LINK_TTL_MINUTES,
        )

        audit_svc.log(
            event='login.send-email-code',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )
        return {'is_valid': True, 'code': 0, 'data': {'ok': True}}

    @staticmethod
    def _token_invalid(*, audit_svc: Any, meta: Any) -> dict[str, Any]:
        """Respuesta 401 TOKEN_INVALID."""
        audit_svc.log(
            event='login.send-email-code',
            success=False,
            error_code='TOKEN_INVALID',
            ip=meta.ip,
        )
        return {
            'is_valid': False,
            'code': 4003,
            'status': 401,
            'data': {'error': 'TOKEN_INVALID'},
        }
