"""WebAuthn service: orquesta `shared.auth.webauthn` + `auth_webauthn_credentials`.

Envuelve los wrappers de fido2 con la config RP por env (RP_ID, RP_NAME,
allowed origins) + las ops de DB. Maneja:
- AC-27: revocar sesiones al registrar el PRIMER metodo MFA (0 -> 1).
- AC-15: clone detection -> marca el credential `disabled_at` + re-raise.

Devuelve primitivos (bytes / list[dict]), NUNCA objetos ORM detached.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from shared.auth.webauthn import (
    WebauthnCloneError,
    build_login_options,
    build_register_options,
    verify_authentication,
    verify_registration,
)
from shared.db.repositories.auth_mfa import (
    count_active_mfa,
    delete_webauthn_credential,
    disable_webauthn_credential,
    get_webauthn_credentials,
    insert_webauthn_credential,
    update_sign_count,
)
from shared.db.session import db_session

from .session_service import SessionService


class WebauthnService:
    """Wrapper de fido2 + DB ops de credentials WebAuthn."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def _rp(self) -> dict[str, Any]:
        return {
            'rp_id': self.app_config.webauthn_rp_id,  # type: ignore[attr-defined]
            'rp_name': self.app_config.webauthn_rp_name,  # type: ignore[attr-defined]
            'expected_origins': self.app_config.webauthn_origins,  # type: ignore[attr-defined]
        }

    def list_credential_ids(self, *, user_id: UUID | str) -> list[bytes]:
        with db_session() as session:
            return [
                bytes(cred.credential_id)
                for cred in get_webauthn_credentials(
                    session,
                    user_id=str(user_id),
                )
            ]

    def list_credentials(self, *, user_id: UUID | str) -> list[dict]:
        """Credentials activos del user como dicts (ordenados last_used DESC)."""
        with db_session() as session:
            return [
                {
                    'credential_id': str(cred.id),
                    'nickname': cred.nickname,
                    'transports': cred.transports,
                    'created_at': cred.created_at.isoformat(),
                    'last_used_at': (
                        cred.last_used_at.isoformat()
                        if cred.last_used_at is not None
                        else None
                    ),
                }
                for cred in get_webauthn_credentials(
                    session,
                    user_id=str(user_id),
                )
            ]

    def build_register_options(
        self,
        *,
        user_id: UUID | str,
        user_name: str,
    ) -> tuple[dict, dict]:
        existing = self.list_credential_ids(user_id=user_id)
        return build_register_options(
            **self._rp(),
            user_id=UUID(str(user_id)).bytes,
            user_name=user_name,
            user_display_name=user_name,
            existing_credentials=existing,
        )

    def verify_registration(
        self,
        *,
        state: dict,
        response: dict,
    ) -> dict[str, Any]:
        return verify_registration(**self._rp(), state=state, response=response)

    def persist_credential(
        self,
        *,
        user_id: UUID | str,
        cred_data: dict,
        nickname: str | None,
    ) -> None:
        """INSERT del credential. Si es el primer MFA del user, revoca sesiones."""
        aaguid_bytes = cred_data.get('aaguid')
        aaguid = str(UUID(bytes=aaguid_bytes)) if aaguid_bytes else None
        revoke = False
        with db_session() as session:
            before = count_active_mfa(session, user_id=str(user_id))
            insert_webauthn_credential(
                session,
                user_id=str(user_id),
                credential_id=cred_data['credential_id'],
                public_key=cred_data['public_key'],
                sign_count=cred_data['sign_count'],
                transports=cred_data.get('transports'),
                attestation_format=cred_data.get('attestation_format'),
                aaguid=aaguid,
                nickname=nickname,
            )
            after = count_active_mfa(session, user_id=str(user_id))
            revoke = before == 0 and after == 1
        if revoke:
            SessionService(self.app_config).revoke_all_for_user(
                user_id=user_id,
            )

    def build_login_options(self, *, user_id: UUID | str) -> tuple[dict, dict]:
        creds = self.list_credential_ids(user_id=user_id)
        return build_login_options(**self._rp(), allowed_credentials=creds)

    def has_credentials(self, *, user_id: UUID | str) -> bool:
        return bool(self.list_credential_ids(user_id=user_id))

    def verify_login(
        self,
        *,
        user_id: UUID | str,
        state: dict,
        response: dict,
    ) -> bytes:
        """Valida la assertion + clone detection + avanza sign_count.

        Raises:
            WebauthnCloneError: sign_count regreso -> marca el credential
            `disabled_at` (AC-15) y re-lanza.
            WebauthnVerifyError: assertion invalida.
        """
        with db_session() as session:
            stored = [
                {
                    'credential_id': bytes(cred.credential_id),
                    'public_key': bytes(cred.public_key),
                    'sign_count': cred.sign_count,
                }
                for cred in get_webauthn_credentials(
                    session,
                    user_id=str(user_id),
                )
            ]
        try:
            result = verify_authentication(
                **self._rp(),
                state=state,
                response=response,
                stored_credentials=stored,
            )
        except WebauthnCloneError as exc:
            with db_session() as session:
                disable_webauthn_credential(
                    session,
                    credential_id=exc.credential_id,
                )
            raise
        with db_session() as session:
            update_sign_count(
                session,
                credential_id=result['credential_id'],
                new_count=result['new_sign_count'],
            )
        return result['credential_id']

    def delete(self, *, user_id: UUID | str, record_id: UUID | str) -> bool:
        with db_session() as session:
            return delete_webauthn_credential(
                session,
                user_id=str(user_id),
                record_id=str(record_id),
            )

    def count_active(self, *, user_id: UUID | str) -> int:
        with db_session() as session:
            return count_active_mfa(session, user_id=str(user_id))
