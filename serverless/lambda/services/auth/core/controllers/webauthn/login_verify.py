"""Controller `webauthn.login-verify` — valida la assertion + emite tokens.

NO requiere auth (es el cierre del login con passkey). Consume el
challenge, valida la assertion (signature + sign_count monotonico). Si el
sign_count regreso -> clone detected (el service deshabilita el credential
y re-lanza). Si OK, emite access+refresh con family nuevo.

AC cubiertos: AC-14, AC-15.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from models.webauthn import WebauthnLoginVerifyIn
from services.audit_service import AuditService
from services.challenge_service import ChallengeService
from services.jwt_service import JwtService
from services.mfa_method_service import MfaMethodService
from services.rate_limit_service import RateLimitService
from services.webauthn_service import WebauthnService
from settings.config import app_config
from shared.auth.jwt import JwtError
from shared.auth.webauthn import WebauthnCloneError, WebauthnVerifyError
from shared.lambda_kit.base_controller import BaseController

from ..login._mfa_login import decide_mfa_step, parse_satisfied

_ENDPOINT = '/auth#webauthn.login-verify'
_MFA_FLOW = 'login-mfa'


class LoginVerify(BaseController):
    """Valida la assertion + emite tokens (action `login-verify`)."""

    event_model = WebauthnLoginVerifyIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. Sin Turnstile."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: WebauthnLoginVerifyIn = (
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
        """Consume el challenge + valida la assertion + emite tokens.

        Returns:
            400 WEBAUTHN_CHALLENGE_NOT_FOUND si el challenge no existe.
            401 WEBAUTHN_CLONE_DETECTED si el sign_count regreso (AC-15).
            401 WEBAUTHN_VERIFY_FAILED si la assertion es invalida.
            200 `{access_token, refresh_token, ...}` si OK (AC-14).
        """
        data: WebauthnLoginVerifyIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        jwt_svc = JwtService(app_config)
        webauthn_svc = WebauthnService(app_config)
        challenge_svc = ChallengeService(app_config)
        audit_svc = AuditService(app_config)

        challenge = challenge_svc.get_and_consume(
            challenge_id=data.challenge_id,
        )
        if challenge is None:
            return {
                'is_valid': False,
                'code': 4007,
                'status': 400,
                'data': {'error': 'WEBAUTHN_CHALLENGE_NOT_FOUND'},
            }

        user_id = challenge['user_id']
        try:
            webauthn_svc.verify_login(
                user_id=user_id,
                state=challenge['state'],
                response=data.response,
            )
        except WebauthnCloneError:
            audit_svc.log(
                event='webauthn.login.clone_detected',
                success=False,
                user_id=user_id,
                error_code='WEBAUTHN_CLONE_DETECTED',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4004,
                'status': 401,
                'data': {'error': 'WEBAUTHN_CLONE_DETECTED'},
            }
        except WebauthnVerifyError:
            audit_svc.log(
                event='webauthn.login-verify',
                success=False,
                user_id=user_id,
                error_code='WEBAUTHN_VERIFY_FAILED',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 4004,
                'status': 401,
                'data': {'error': 'WEBAUTHN_VERIFY_FAILED'},
            }

        # Multi-factor: la passkey cuenta como factor 'webauthn' satisfecho,
        # ACUMULANDO los factores previos del checklist. Cuando webauthn es un
        # factor del checklist, el front manda el temp step=2 rolling (flow
        # 'login-mfa[:...]'); de su `flow` se extraen los factores ya hechos
        # (ej. password) y se le suma 'webauthn'. Sin temp (login passwordless
        # directo) el unico satisfecho es 'webauthn'. El temp se valida (typ +
        # flow + step + que su `sub` sea el user del challenge: anti
        # cross-account) y se blacklistea (rolling); un temp invalido degrada a
        # solo 'webauthn' (el challenge ya autentica al user, no se rompe el
        # passwordless).
        satisfied = ['webauthn']
        if data.temp_token:
            satisfied = self._satisfied_from_temp(
                jwt_svc=jwt_svc,
                temp_token=data.temp_token,
                user_id=user_id,
            )
        data_out = decide_mfa_step(
            jwt_svc=jwt_svc,
            app_config=app_config,
            user_id=user_id,
            satisfied=satisfied,
            required=MfaMethodService(app_config).required_methods(
                user_id=user_id,
            ),
            ip=meta.ip,
            country=meta.country,
            user_agent=meta.user_agent,
        )

        audit_svc.log(
            event='webauthn.login.success',
            success=True,
            user_id=user_id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        return {'is_valid': True, 'code': 0, 'data': data_out}

    def _satisfied_from_temp(
        self,
        *,
        jwt_svc: JwtService,
        temp_token: str,
        user_id: str,
    ) -> list[str]:
        """`[*factores previos del temp, 'webauthn']` validando + rotando el temp.

        El temp debe ser un step=2 del checklist (`typ='temp'`, flow
        `login-mfa[:...]`) cuyo `sub` sea el user del challenge (anti
        cross-account). Si valida, blacklistea su `jti` (rolling) y devuelve los
        factores previos + 'webauthn'. Si NO valida (token invalido, flow/step
        equivocado, o sub de otro user), degrada a `['webauthn']`: el challenge
        ya autentico al user, no se rompe el passwordless directo.
        """
        try:
            claims = jwt_svc.verify(temp_token, expected_typ='temp')
        except JwtError:
            return ['webauthn']
        flow_ok = (
            claims.flow is not None
            and claims.flow.split(':', 1)[0] == _MFA_FLOW
        )
        if not flow_ok or claims.step != 2 or str(claims.sub) != str(user_id):
            return ['webauthn']
        jwt_svc.blacklist(
            jti=claims.jti,
            exp=claims.exp,
            user_id=user_id,
            reason='rotation',
        )
        return [*parse_satisfied(claims.flow), 'webauthn']
