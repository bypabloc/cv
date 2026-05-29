"""Controller `profile.change-email` — inicia el cambio de email (AC-4).

Requiere access JWT. Valida que el nuevo email este libre; si el user
tiene password, la valida con argon2; genera un magic-link al email NUEVO
(token opaco, hash en Neon, `{new_email}` en metadata) y publica el email
de confirmacion a la cola del worker. Devuelve 200 con un request_id.
"""

from __future__ import annotations

from typing import Any

from models.profile import ProfileChangeEmailIn
from services.audit_service import AuditService
from services.email_dispatch_service import EmailDispatchService
from services.jwt_service import require_active_user
from services.profile_service import ProfileService
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.core.ulid import new_uuidv7
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/users#profile.change-email'


class ChangeEmail(BaseController):
    """Inicia el cambio de email del propio user (action `change-email`)."""

    event_model = ProfileChangeEmailIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP."""
        base = super().validate()
        if not base.get('is_valid'):
            return base
        meta = self.validated_data.meta  # type: ignore[union-attr]
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '', endpoint=_ENDPOINT, country=meta.country,
        )
        return base

    def execute(self) -> dict[str, Any]:
        """Genera el magic-link + publica el email de confirmacion.

        Returns:
            409 EMAIL_ALREADY_IN_USE si el nuevo email ya esta en uso.
            401 INVALID_PASSWORD si el user tiene password y no matchea.
            200 {request_id, expires_in} si el email de confirmacion se encolo.
        """
        data: ProfileChangeEmailIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        user = require_active_user(meta.authorization, app_config=app_config)

        new_email = str(data.new_email).strip().lower()
        svc = ProfileService(app_config)

        if svc.get_by_email(email=new_email) is not None:
            return {
                'is_valid': False,
                'code': 4004,
                'status': 409,
                'data': {'error': 'EMAIL_ALREADY_IN_USE'},
            }

        if svc.has_password(user_id=user.id) and (
            not data.password
            or not svc.verify_password(
                user_id=user.id, password=data.password,
            )
        ):
            return {
                'is_valid': False,
                'code': 4005,
                'status': 401,
                'data': {'error': 'INVALID_PASSWORD'},
            }

        plain, ttl_seconds = svc.create_email_change_link(
            user_id=user.id,
            new_email=new_email,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )
        verify_url = (
            f'{app_config.users_base_url}'
            f'?operation=profile&action=confirm-email-change&token={plain}'
        )
        EmailDispatchService(app_config).publish_email_change_verify(
            to=new_email,
            user_id=user.id,
            niche=None,
            new_email=new_email,
            verify_url=verify_url,
            expires_in_min=ttl_seconds // 60,
        )
        AuditService(app_config).log(
            event='profile.change-email.requested',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        return {
            'is_valid': True,
            'code': 0,
            'data': {'request_id': new_uuidv7(), 'expires_in': ttl_seconds},
        }
