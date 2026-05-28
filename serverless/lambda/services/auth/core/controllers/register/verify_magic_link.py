"""Controller `register.verify-magic-link` — confirma el email via link.

El visitante clickea el link recibido por email. El controller resuelve
el token opaco (SHA-256 del plain) contra `auth_magic_links`, consume
single-use, activa al user y emite access + refresh JWTs.

http_handler NO soporta HTTP 302 nativamente: la respuesta es un JSON
200 con `redirect_url` en el body. El frontend (dashboard) hace el
redirect del lado cliente al `dashboard_callback_url#access=...&...`.

AC cubiertos: AC-3, AC-16, AC-17.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from models.register import RegisterVerifyMagicLinkIn
from services.audit_service import AuditService
from services.jwt_service import JwtService
from services.magic_link_service import MagicLinkService
from services.rate_limit_service import RateLimitService
from services.user_service import UserService
from settings.config import app_config

from shared.core.ulid import new_uuidv7
from shared.lambda_kit import BaseController

_ENDPOINT = '/auth#register.verify-magic-link'


class VerifyMagicLink(BaseController):
    """Verifica el magic-link del registro (action `verify-magic-link`)."""

    event_model = RegisterVerifyMagicLinkIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit. Sin Turnstile (ya valido en start)."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: RegisterVerifyMagicLinkIn = (
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
        """Consume el link + emite access/refresh + redirect al dashboard.

        Returns:
            En exito: `{is_valid: True, code: 0, data: {redirect_url,
            access_token, refresh_token, user: {...}}}` (HTTP 200).
            link consumido (`LINK_CONSUMED`): `{is_valid: False, code:
            4006, status: 400, data: {error}}`.
            link expirado o inexistente (`LINK_EXPIRED`): `{is_valid:
            False, code: 4007, status: 400, data: {error}}`.
        """
        data: RegisterVerifyMagicLinkIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        link_svc = MagicLinkService(app_config)
        user_svc = UserService(app_config)
        jwt_svc = JwtService(app_config)
        audit_svc = AuditService(app_config)

        consumed = link_svc.verify(plain=data.token)
        if consumed is None:
            # Distinguir el motivo del fallo.
            state = link_svc.get_state(plain=data.token)
            if state is not None and state.consumed_at is not None:
                audit_svc.log(
                    event='register.verify-magic-link',
                    success=False,
                    error_code='LINK_CONSUMED',
                    ip=meta.ip,
                    user_agent=meta.user_agent,
                )
                return {
                    'is_valid': False,
                    'code': 4006,
                    'status': 400,
                    'data': {'error': 'LINK_CONSUMED'},
                }
            # state is None o expirado: agrupado bajo LINK_EXPIRED (anti
            # enumeration: no revelamos si el link existia o no).
            audit_svc.log(
                event='register.verify-magic-link',
                success=False,
                error_code='LINK_EXPIRED',
                ip=meta.ip,
                user_agent=meta.user_agent,
            )
            return {
                'is_valid': False,
                'code': 4007,
                'status': 400,
                'data': {'error': 'LINK_EXPIRED'},
            }

        user = user_svc.get_by_id(str(consumed.user_id))
        if user is None:
            audit_svc.log(
                event='register.verify-magic-link',
                success=False,
                error_code='USER_NOT_FOUND',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'EMAIL_NOT_FOUND'},
            }

        user_svc.mark_active(user)

        access_token, _ = jwt_svc.issue_access(user_id=user.id)
        family_id = UUID(new_uuidv7())
        refresh_token, _ = jwt_svc.issue_refresh(
            user_id=user.id, family_id=family_id,
        )

        audit_svc.log(
            event='register.verify-magic-link',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        redirect_url = (
            f'{app_config.dashboard_callback_url}'
            f'#access={access_token}'
            f'&refresh={refresh_token}'
            f'&user_id={user.id}'
            f'&email={user.email}'
        )
        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'redirect_url': redirect_url,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': 900,
                'token_type': 'Bearer',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'status': user.status.value,
                },
            },
        }
