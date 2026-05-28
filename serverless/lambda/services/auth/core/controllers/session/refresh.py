"""Controller `session.refresh` — rota el refresh JWT (access + refresh nuevos).

Verifica el refresh JWT (typ='refresh'). Si el jti ya esta blacklisted
es un REUSO: revoca toda la familia (token theft detection, AC-8). Si es
valido, rota: blacklistea el refresh viejo y emite un par access+refresh
nuevo con el MISMO family_id.

AC cubiertos: AC-7 (rotation), AC-8 (reuse detection), AC-10 (invalid).
"""

from __future__ import annotations

from typing import Any

from models.session import SessionRefreshIn
from services.audit_service import AuditService
from services.jwt_service import JwtService
from services.rate_limit_service import RateLimitService
from settings.config import app_config

from shared.auth import JwtExpiredError, JwtInvalidError
from shared.lambda_kit import BaseController

_ENDPOINT = '/auth#session.refresh'


class Refresh(BaseController):
    """Rota el refresh JWT (action `refresh`)."""

    event_model = SessionRefreshIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: SessionRefreshIn = (
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
        """Verifica refresh, detecta reuso o rota.

        Returns:
            En exito: `{is_valid: True, code: 0, data: {access_token,
            refresh_token, expires_in}}`.
            Reuso detectado: 401 TOKEN_REUSE_DETECTED + familia revocada
            (AC-8).
            Invalido / expirado: 401 (AC-10).
        """
        data: SessionRefreshIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        jwt_svc = JwtService(app_config)
        audit_svc = AuditService(app_config)

        # Verifica signature + exp + typ SIN chequear blacklist: necesitamos
        # el family_id del refresh aunque este revocado, para poder revocar
        # toda la familia en el caso de reuso.
        try:
            claims = jwt_svc.verify_allow_revoked(
                data.refresh_token, expected_typ='refresh',
            )
        except JwtExpiredError:
            audit_svc.log(
                event='session.refresh',
                success=False,
                error_code='REFRESH_EXPIRED',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4003,
                'status': 401,
                'data': {'error': 'REFRESH_EXPIRED'},
            }
        except JwtInvalidError:
            audit_svc.log(
                event='session.refresh',
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

        # Reuso detectado: el refresh ya fue rotado (su jti esta en la
        # blacklist). Revoca TODA la familia y rechaza (AC-8).
        if jwt_svc.is_blacklisted(jti=claims.jti):
            if claims.family_id is not None:
                jwt_svc.revoke_family(
                    family_id=claims.family_id,
                    user_id=claims.sub,
                    exp=claims.exp,
                )
            audit_svc.log(
                event='session.refresh.reuse_detected',
                success=False,
                user_id=claims.sub,
                error_code='TOKEN_REUSE_DETECTED',
                ip=meta.ip,
                meta_data={
                    'jti': str(claims.jti),
                    'family_id': (
                        str(claims.family_id)
                        if claims.family_id is not None
                        else None
                    ),
                },
            )
            return {
                'is_valid': False,
                'code': 4004,
                'status': 401,
                'data': {'error': 'TOKEN_REUSE_DETECTED'},
            }

        # Rotation normal: blacklistea el refresh viejo + emite nuevos
        # tokens con el MISMO family_id.
        jwt_svc.blacklist(
            jti=claims.jti,
            exp=claims.exp,
            user_id=claims.sub,
            reason='rotation',
            family_id=claims.family_id,
        )
        access_token, _ = jwt_svc.issue_access(user_id=claims.sub)
        refresh_token, _ = jwt_svc.issue_refresh(
            user_id=claims.sub, family_id=claims.family_id,
        )

        audit_svc.log(
            event='session.refresh',
            success=True,
            user_id=claims.sub,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': 900,
                'token_type': 'Bearer',
            },
        }
