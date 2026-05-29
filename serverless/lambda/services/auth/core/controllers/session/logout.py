"""Controller `session.logout` — revoca el access JWT (+ familia refresh).

Verifica el access JWT, lo blacklistea y, si llega el refresh, revoca
toda su familia (Query GSI by_family_id + BatchWrite). Idempotente: si
el jti ya esta blacklisted devuelve 204 igual.

AC cubiertos: AC-9 (logout), AC-23 (idempotente).
"""

from __future__ import annotations

from typing import Any

from models.session import SessionLogoutIn
from services.audit_service import AuditService
from services.jwt_service import JwtService
from services.rate_limit_service import RateLimitService
from services.session_tracking_service import SessionTrackingService
from settings.config import app_config
from shared.auth import JwtError
from shared.lambda_kit import BaseController

_ENDPOINT = '/auth#session.logout'


class Logout(BaseController):
    """Revoca la sesion del user (action `logout`)."""

    event_model = SessionLogoutIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: SessionLogoutIn = (
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
        """Blacklistea el access (+ familia refresh). Idempotente.

        Returns:
            204 siempre que el access JWT sea valido (incluso si ya
            estaba blacklisted, AC-23).
            401 TOKEN_INVALID si el access no verifica (signature/exp).
        """
        data: SessionLogoutIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        jwt_svc = JwtService(app_config)
        audit_svc = AuditService(app_config)

        # Verifica el access SIN exigir que NO este blacklisted: el
        # logout es idempotente (AC-23). verify_allow_revoked valida
        # signature + exp + typ pero no rechaza por blacklist.
        try:
            access_claims = jwt_svc.verify_allow_revoked(
                data.access_token,
                expected_typ='access',
            )
        except JwtError:
            audit_svc.log(
                event='session.logout',
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

        # Idempotencia: si ya estaba blacklisted, no re-blacklistear.
        if not jwt_svc.is_blacklisted(jti=access_claims.jti):
            jwt_svc.blacklist(
                jti=access_claims.jti,
                exp=access_claims.exp,
                user_id=access_claims.sub,
                reason='logout',
            )

        # Si llega refresh, revoca toda su familia. Un refresh invalido
        # NO invalida el logout (el access ya quedo revocado).
        if data.refresh_token is not None:
            try:
                refresh_claims = jwt_svc.verify_allow_revoked(
                    data.refresh_token,
                    expected_typ='refresh',
                )
            except JwtError:
                refresh_claims = None
            if (
                refresh_claims is not None
                and refresh_claims.family_id is not None
            ):
                jwt_svc.revoke_family(
                    family_id=refresh_claims.family_id,
                    user_id=refresh_claims.sub,
                    exp=refresh_claims.exp,
                )
                # Borra la sesion trackeada de esa family (AC-24).
                SessionTrackingService(app_config).on_session_revoked(
                    family_id=refresh_claims.family_id,
                )

        audit_svc.log(
            event='session.logout',
            success=True,
            user_id=access_claims.sub,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        return {
            'is_valid': True,
            'code': 0,
            'status': 204,
            'data': {},
        }
