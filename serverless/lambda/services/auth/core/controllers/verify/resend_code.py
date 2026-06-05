"""Controller `verify.resend-code` — re-emite code + magic-link nuevos.

Verifica el rolling temp_token (typ='temp'), aplica un throttle propio
(min 60s desde la ultima emision para ese user/flow, AC-21), invalida
los artefactos previos, genera un code + magic-link nuevos, los publica
al worker y rota el temp (step+1).

AC cubiertos: AC-19 (re-emision), AC-21 (throttle).
"""

from __future__ import annotations

from typing import Any

from models.verify import VerifyResendCodeIn
from services.audit_service import AuditService
from services.code_service import CodeService
from services.email_dispatch_service import EmailDispatchService
from services.flow_service import FlowService
from services.jwt_service import JwtService
from services.magic_link_service import LINK_TTL_MINUTES, MagicLinkService
from services.rate_limit_service import RateLimitService
from services.user_service import UserService
from settings.config import app_config
from shared.auth.jwt import JwtExpiredError, JwtInvalidError, JwtRevokedError
from shared.db.models.auth.enums import AuthCodeKind, AuthLinkKind
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#verify.resend-code'

# Map flow del temp JWT -> kinds del code / magic-link. El flujo de entrada
# es `login` unico (register eliminado): el unico flow que re-emite es login.
_FLOW_TO_KINDS = {
    'login': (AuthCodeKind.LOGIN, AuthLinkKind.LOGIN),
}


class ResendCode(BaseController):
    """Re-emite code + magic-link (action `resend-code`)."""

    event_model = VerifyResendCodeIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: VerifyResendCodeIn = (
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
        """Verifica temp_token + throttle, re-emite artefactos, rota temp.

        Returns:
            En exito: `{is_valid: True, code: 0, data: {temp_token,
            expires_in: 300}}`.
            Throttle activo: 429 RESEND_THROTTLED (AC-21).
            temp_token expirado / blacklisted / invalido: 401.
        """
        data: VerifyResendCodeIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        jwt_svc = JwtService(app_config)
        flow_svc = FlowService(app_config)
        user_svc = UserService(app_config)
        code_svc = CodeService(app_config)
        link_svc = MagicLinkService(app_config)
        email_svc = EmailDispatchService(app_config)
        audit_svc = AuditService(app_config)

        try:
            claims = jwt_svc.verify(data.temp_token, expected_typ='temp')
        except JwtExpiredError:
            audit_svc.log(
                event='verify.resend-code',
                success=False,
                error_code='TEMP_TOKEN_EXPIRED',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4018,
                'status': 401,
                'data': {'error': 'TEMP_TOKEN_EXPIRED'},
            }
        except JwtRevokedError:
            return {
                'is_valid': False,
                'code': 4003,
                'status': 401,
                'data': {'error': 'TOKEN_BLACKLISTED'},
            }
        except JwtInvalidError:
            return {
                'is_valid': False,
                'code': 4003,
                'status': 401,
                'data': {'error': 'TOKEN_INVALID'},
            }

        user = user_svc.get_by_id(str(claims.sub))
        if user is None:
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'EMAIL_NOT_FOUND'},
            }

        kind_code, kind_link = _FLOW_TO_KINDS.get(
            claims.flow or 'login',
            (AuthCodeKind.LOGIN, AuthLinkKind.LOGIN),
        )

        # Throttle: minimo 60s desde el ultimo code (AC-21).
        retry_after = code_svc.seconds_until_resend_allowed(
            user_id=user.id,
            kind=kind_code,
        )
        if retry_after > 0:
            audit_svc.log(
                event='verify.resend-code',
                success=False,
                user_id=user.id,
                error_code='RESEND_THROTTLED',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4010,
                'status': 429,
                'data': {
                    'error': 'RESEND_THROTTLED',
                    'retry_after': retry_after,
                },
            }

        # Invalida artefactos previos + genera nuevos.
        user_svc.invalidate_active_codes_and_links(
            user_id=str(user.id),
            kind_code=kind_code,
            kind_link=kind_link,
        )
        code, _ = code_svc.generate_and_persist(
            user_id=user.id,
            kind=kind_code,
        )
        token, _ = link_svc.generate_and_persist(
            user_id=user.id,
            kind=kind_link,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        verify_url = (
            f'{app_config.magic_link_base_url}'
            f'?operation={claims.flow}&action=verify-magic-link&token={token}'
        )
        # UN solo email con el magic-link Y el code (alternativas). El kind
        # `<flow>-unified` resuelve a register-unified/login-unified. LINK y
        # CODE comparten TTL (15 min), por eso un solo expires_in_min.
        email_svc.publish_unified(
            to=user.email,
            user_id=user.id,
            niche=None,
            kind=f'{claims.flow}-unified',
            verify_url=verify_url,
            code=code,
            expires_in_min=LINK_TTL_MINUTES,
        )

        # Rota el temp (blacklistea el viejo + step+1).
        new_temp, _ = flow_svc.advance_step(claims)

        audit_svc.log(
            event='verify.resend-code',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'temp_token': new_temp,
                'expires_in': 300,
            },
        }
