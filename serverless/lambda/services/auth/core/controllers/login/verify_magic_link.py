"""Controller `login.verify-magic-link` — login passwordless via link.

Espejo de `register.verify-magic-link` pero para usuarios ya activos.
Tras consumir el link emite access + refresh JWTs y ACTUALIZA
`last_login_at` (AC-22). No marca el user como active (ya lo esta).

AC cubiertos: AC-22.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from models.login import LoginVerifyMagicLinkIn
from services.audit_service import AuditService
from services.jwt_service import JwtService
from services.magic_link_service import MagicLinkService
from services.rate_limit_service import RateLimitService
from services.session_tracking_service import SessionTrackingService
from services.user_service import UserService
from settings.config import app_config
from shared.core.ulid import new_uuidv7
from shared.lambda_kit import BaseController

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

        # AC-22: actualiza last_login_at + resetea failed_attempts.
        user_svc.update_last_login(user)

        family_id = UUID(new_uuidv7())
        access_token, _ = jwt_svc.issue_access(
            user_id=user.id, family_id=family_id,
        )
        refresh_token, _ = jwt_svc.issue_refresh(
            user_id=user.id,
            family_id=family_id,
        )
        SessionTrackingService(app_config).on_session_created(
            user_id=user.id,
            family_id=family_id,
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
