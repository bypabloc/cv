"""Controller `status.revoke-session` — cierra una sesion (AC-9/AC-10).

Requiere access JWT. Borra la sesion indicada (dual filter por user_id) y
blacklistea su family. NO permite revocar la sesion en curso
(CANNOT_REVOKE_CURRENT_SESSION -> usar auth.session.logout).
"""

from __future__ import annotations

from typing import Any

from models.status import StatusRevokeSessionIn
from services.audit_service import AuditService
from services.jwt_service import JwtService, authenticate
from services.rate_limit_service import RateLimitService
from services.session_service import SessionService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController
from shared.observability.metrics import MetricUnit, metrics

_ENDPOINT = '/users#status'


class RevokeSession(BaseController):
    """Cierra una sesion del user (action `revoke-session`)."""

    event_model = StatusRevokeSessionIn

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
        """Borra la sesion + blacklistea su family.

        Returns:
            404 NOT_FOUND si la sesion no existe / no es del user.
            400 CANNOT_REVOKE_CURRENT_SESSION si es la sesion en curso.
            204 si la sesion se cerro.
        """
        data: StatusRevokeSessionIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        user, claims = authenticate(meta.authorization, app_config=app_config)
        session_id = str(data.session_id)

        svc = SessionService(app_config)
        family = svc.get_family(user_id=user.id, session_id=session_id)
        if family is None:
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'NOT_FOUND'},
            }

        current_family = (
            str(claims.family_id) if claims.family_id is not None else None
        )
        if current_family is not None and family == current_family:
            return {
                'is_valid': False,
                'code': 4006,
                'status': 400,
                'data': {'error': 'CANNOT_REVOKE_CURRENT_SESSION'},
            }

        svc.revoke_session(user_id=user.id, session_id=session_id)
        JwtService(app_config).revoke_families(
            family_ids=[family], user_id=user.id,
        )
        AuditService(app_config).log(
            event='status.revoke-session',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
            meta_data={'session_id': session_id},
        )
        metrics.add_metric(
            name='UsersSessionRevoked', unit=MetricUnit.Count, value=1,
        )

        return {'is_valid': True, 'code': 0, 'status': 204, 'data': {}}
