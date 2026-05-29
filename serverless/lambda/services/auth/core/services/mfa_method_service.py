"""MFA method service: orquesta `auth_mfa_methods` (TOTP + email_code).

Envuelve el repository `shared.db.repositories.auth_mfa` con la logica de
sesion + el side-effect de AC-27 (revocar las sesiones del user al
confirmar su PRIMER metodo MFA — transicion total_mfa 0 -> 1).

Devuelve primitivos (bool / list[dict] / bytes), NUNCA objetos ORM
detached, para que los controllers no toquen la sesion.
"""

from __future__ import annotations

from uuid import UUID

from shared.db.models.auth import AuthMfaKind
from shared.db.repositories.auth_mfa import (
    confirm_mfa,
    count_active_mfa,
    disable_mfa,
    get_mfa_method,
    list_mfa_methods,
    mark_method_used,
    set_preferred,
    upsert_totp_method,
)
from shared.db.session import db_session

from .session_service import SessionService


class MfaMethodService:
    """CRUD de `auth_mfa_methods` + revocacion de sesiones en el primer MFA."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def list_active(self, *, user_id: UUID | str) -> list[dict]:
        """Metodos activos del user como dicts serializables."""
        with db_session() as session:
            methods = list_mfa_methods(session, user_id=str(user_id))
            return [
                {
                    'kind': method.kind.value,
                    'preferred': method.preferred,
                    'confirmed': method.confirmed_at is not None,
                }
                for method in methods
            ]

    def confirmed_kinds(self, *, user_id: UUID | str) -> list[str]:
        """Kinds de los metodos confirmados y activos del user."""
        with db_session() as session:
            return [
                method.kind.value
                for method in list_mfa_methods(session, user_id=str(user_id))
                if method.confirmed_at is not None
            ]

    def upsert_pending_totp(
        self,
        *,
        user_id: UUID | str,
        ciphertext: bytes,
    ) -> None:
        """Crea/reusa el row TOTP pendiente (confirmed_at=NULL)."""
        with db_session() as session:
            upsert_totp_method(
                session,
                user_id=str(user_id),
                ciphertext=ciphertext,
            )

    def get_totp_ciphertext(
        self,
        *,
        user_id: UUID | str,
        require_confirmed: bool,
    ) -> bytes | None:
        """Ciphertext del secret TOTP del user, o None.

        `require_confirmed=True` exige el metodo confirmado y no
        deshabilitado (login); `False` acepta el pendiente (confirm-totp).
        """
        with db_session() as session:
            method = get_mfa_method(
                session,
                user_id=str(user_id),
                kind=AuthMfaKind.TOTP,
            )
            if method is None or method.totp_secret_ciphertext is None:
                return None
            if require_confirmed and (
                method.confirmed_at is None or method.disabled_at is not None
            ):
                return None
            return bytes(method.totp_secret_ciphertext)

    def confirm(self, *, user_id: UUID | str, kind: AuthMfaKind) -> bool:
        """Confirma el metodo. Si es el primer MFA del user, revoca sesiones."""
        revoke = False
        with db_session() as session:
            before = count_active_mfa(session, user_id=str(user_id))
            method = confirm_mfa(session, user_id=str(user_id), kind=kind)
            if method is None:
                return False
            confirmed = [
                m
                for m in list_mfa_methods(session, user_id=str(user_id))
                if m.confirmed_at is not None
            ]
            if len(confirmed) == 1:
                method.preferred = True
                session.flush()
            after = count_active_mfa(session, user_id=str(user_id))
            revoke = before == 0 and after == 1
        if revoke:
            SessionService(self.app_config).revoke_all_for_user(
                user_id=user_id,
            )
        return True

    def setup_email_code(self, *, user_id: UUID | str) -> bool:
        """Activa email_code como metodo MFA (confirmado de inmediato).

        El user ya puede recibir email (lo probo en register), asi que el
        metodo se inserta confirmado. Si es el primer MFA, revoca sesiones.
        """
        revoke = False
        with db_session() as session:
            before = count_active_mfa(session, user_id=str(user_id))
            existing = get_mfa_method(
                session,
                user_id=str(user_id),
                kind=AuthMfaKind.EMAIL_CODE,
            )
            if existing is None:
                from datetime import UTC, datetime

                from shared.db.models.auth import AuthMfaMethod

                method = AuthMfaMethod(
                    user_id=str(user_id),
                    kind=AuthMfaKind.EMAIL_CODE,
                    confirmed_at=datetime.now(tz=UTC),
                )
                session.add(method)
            else:
                confirm_mfa(
                    session,
                    user_id=str(user_id),
                    kind=AuthMfaKind.EMAIL_CODE,
                )
            session.flush()
            after = count_active_mfa(session, user_id=str(user_id))
            revoke = before == 0 and after == 1
        if revoke:
            SessionService(self.app_config).revoke_all_for_user(
                user_id=user_id,
            )
        return True

    def set_preferred(self, *, user_id: UUID | str, kind: AuthMfaKind) -> bool:
        """Marca `kind` como preferido. False si el user no tiene ese metodo."""
        with db_session() as session:
            method = get_mfa_method(
                session,
                user_id=str(user_id),
                kind=kind,
            )
            if method is None or method.disabled_at is not None:
                return False
            set_preferred(session, user_id=str(user_id), kind=kind)
        return True

    def disable(self, *, user_id: UUID | str, kind: AuthMfaKind) -> bool:
        """Deshabilita el metodo. False si no existe (controller valida count)."""
        with db_session() as session:
            return disable_mfa(session, user_id=str(user_id), kind=kind)

    def count_active(self, *, user_id: UUID | str) -> int:
        """Cuenta transversal de metodos MFA activos (MUST_KEEP_ONE)."""
        with db_session() as session:
            return count_active_mfa(session, user_id=str(user_id))

    def has_active_method(
        self,
        *,
        user_id: UUID | str,
        kind: AuthMfaKind,
    ) -> bool:
        """True si el user tiene el metodo `kind` activo (no deshabilitado)."""
        with db_session() as session:
            method = get_mfa_method(
                session,
                user_id=str(user_id),
                kind=kind,
            )
            return method is not None and method.disabled_at is None

    def mark_used(self, *, user_id: UUID | str, kind: AuthMfaKind) -> None:
        """Setea last_used_at del metodo (login con TOTP exitoso)."""
        with db_session() as session:
            mark_method_used(session, user_id=str(user_id), kind=kind)
