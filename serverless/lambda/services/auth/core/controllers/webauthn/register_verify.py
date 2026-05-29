"""Controller `webauthn.register-verify` — valida la attestation + guarda credential.

Requiere access JWT valido. Consume el challenge (single-use), valida la
attestation criptografica y persiste el credential. Side-effect AC-27 si
es el primer MFA (lo gestiona el service).

AC cubiertos: AC-12.
"""

from __future__ import annotations

from typing import Any

from models.webauthn import WebauthnRegisterVerifyIn
from services.audit_service import AuditService
from services.auth_service import require_active_user
from services.challenge_service import ChallengeService
from services.webauthn_service import WebauthnService
from settings.config import app_config
from shared.auth import WebauthnVerifyError
from shared.lambda_kit import BaseController


class RegisterVerify(BaseController):
    """Valida y guarda un passkey nuevo (action `register-verify`)."""

    event_model = WebauthnRegisterVerifyIn

    def execute(self) -> dict[str, Any]:
        """Consume el challenge + valida la attestation + persiste.

        Returns:
            400 WEBAUTHN_CHALLENGE_NOT_FOUND si el challenge no existe.
            404 NOT_FOUND si el challenge es de otro user.
            400 WEBAUTHN_REGISTRATION_FAILED si la attestation es invalida.
            201 `{credential_id, nickname}` si OK.
        """
        data: WebauthnRegisterVerifyIn = (
            self.validated_data  # type: ignore[assignment]
        )
        meta = data.meta

        user = require_active_user(meta.authorization, app_config=app_config)

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
        if str(challenge['user_id']) != str(user.id):
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {'error': 'NOT_FOUND'},
            }

        try:
            cred_data = webauthn_svc.verify_registration(
                state=challenge['state'],
                response=data.response,
            )
        except WebauthnVerifyError:
            audit_svc.log(
                event='webauthn.register-verify',
                success=False,
                user_id=user.id,
                error_code='WEBAUTHN_REGISTRATION_FAILED',
                ip=meta.ip,
            )
            return {
                'is_valid': False,
                'code': 1002,
                'status': 400,
                'data': {'error': 'WEBAUTHN_REGISTRATION_FAILED'},
            }

        webauthn_svc.persist_credential(
            user_id=user.id,
            cred_data=cred_data,
            nickname=data.nickname,
        )

        audit_svc.log(
            event='webauthn.register-verify',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        return {
            'is_valid': True,
            'code': 0,
            'status': 201,
            'data': {'nickname': data.nickname},
        }
