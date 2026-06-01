"""Controller `profile.change-password` — cambia la password del propio user.

Requiere access JWT. Verifica `current_password` contra el hash argon2,
hashea `new_password` con argon2id y REVOCA las demas sesiones del user
(blacklist de families de refresh) dejando viva SOLO la sesion en curso.

Preservar la sesion actual: se obtiene `family_id` de la sesion en curso
desde el access JWT (`authenticate`), se listan las sesiones del user y se
revocan UNA A UNA todas menos la actual (`revoke_session` borra la fila de
DB y devuelve su family_id); luego se blacklistean esas families. La fila
de la sesion actual NO se borra y su family NUNCA se blacklistea.
"""

from __future__ import annotations

from typing import Any

from models.profile import ProfileChangePasswordIn
from services.audit_service import AuditService
from services.email_dispatch_service import EmailDispatchService
from services.jwt_service import JwtService, authenticate
from services.profile_service import ProfileService
from services.rate_limit_service import RateLimitService
from services.session_service import SessionService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController
from shared.observability.metrics import MetricUnit, metrics

_ENDPOINT = '/users#profile.change-password'


class ChangePassword(BaseController):
    """Cambia la password del propio user (action `change-password`)."""

    event_model = ProfileChangePasswordIn

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
        """Verifica current, hashea new, revoca las demas sesiones.

        Returns:
            401 INVALID_PASSWORD si la password actual no matchea (NO
                actualiza nada).
            200 {is_valid, code:0, data:{ok:true}} si la password se
                cambio y las demas sesiones se revocaron.
        """
        data: ProfileChangePasswordIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        user, claims = authenticate(meta.authorization, app_config=app_config)
        current_family_id = (
            str(claims.family_id) if claims.family_id is not None else None
        )

        updated = ProfileService(app_config).update_password(
            user_id=user.id,
            current_password=data.current_password,
            new_password=data.new_password,
        )
        if not updated:
            AuditService(app_config).log(
                event='profile.change-password.failed',
                success=False,
                user_id=user.id,
                error_code='INVALID_PASSWORD',
                ip=meta.ip,
                user_agent=meta.user_agent,
            )
            return {
                'is_valid': False,
                'code': 4005,
                'status': 401,
                'data': {'error': 'INVALID_PASSWORD', 'code': 4005},
            }

        # Revoca las demas sesiones (deja viva SOLO la actual): borra cada
        # fila de sesion != actual y blacklistea sus families. La family
        # actual nunca entra a `revoked_families` -> no se blacklistea.
        session_svc = SessionService(app_config)
        revoked_families: list[str] = []
        sessions = session_svc.list_for_user(
            user_id=user.id, current_family_id=current_family_id,
        )
        for sess in sessions:
            if sess.get('current'):
                continue
            family_id = session_svc.revoke_session(
                user_id=user.id, session_id=sess['session_id'],
            )
            if family_id is not None:
                revoked_families.append(family_id)

        if revoked_families:
            JwtService(app_config).revoke_families(
                family_ids=revoked_families, user_id=user.id,
            )

        EmailDispatchService(app_config).publish_password_changed(
            to=user.email, user_id=user.id, niche=None,
        )
        AuditService(app_config).log(
            event='profile.change-password.success',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
            meta_data={'revoked_sessions': len(revoked_families)},
        )
        metrics.add_metric(
            name='UsersPasswordChanged', unit=MetricUnit.Count, value=1,
        )

        return {
            'is_valid': True,
            'code': 0,
            'data': {'is_valid': True, 'code': 0, 'data': {'ok': True}},
        }
