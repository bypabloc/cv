"""Profile service del Lambda `users`.

CRUD de `auth_users` + el flujo change-email. Orquesta los helpers de
`shared.db.repositories.auth_users` (gestion) y `shared.db.repositories.auth`
(lookup por email, credenciales). Cada metodo abre su propio `db_session()`.

`soft_delete` NO borra la fila de `auth_users` (UPDATE de `deleted_at` +
anonimiza email): el repo borra explicito las credenciales/mfa/sessions
porque las FK CASCADE reaccionan a DELETE, no a UPDATE.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from shared.auth.password import verify_password
from shared.auth.tokens import generate_opaque_token, hash_token
from shared.db.models.auth.credentials import AuthCredentials
from shared.db.models.auth.magic_link import AuthMagicLink
from shared.db.models.auth.user import AuthUser
from shared.db.repositories.auth import get_user_by_email
from shared.db.repositories.auth_mfa import (
    count_active_mfa,
    get_webauthn_credentials,
    list_mfa_methods,
)
from shared.db.repositories.auth_users import (
    consume_email_change_link,
    count_remaining_recovery_codes,
    count_user_sessions,
    disable_user,
    enable_user,
    get_user_by_id,
    hard_delete_user,
    insert_email_change_link,
    list_recent_audit,
    list_users_paginated,
    soft_delete_user,
    update_profile,
    update_user_email,
)
from shared.db.session import db_session

# TTL del magic-link de change-email (15 min, igual que register/login).
_EMAIL_CHANGE_TTL = timedelta(minutes=15)


class ProfileService:
    """Service de auth_users (perfil + change-email + delete + admin)."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def get_by_id(self, *, user_id: str) -> AuthUser | None:
        """Lookup por PK. None si no existe."""
        with db_session() as session:
            return get_user_by_id(session, user_id=user_id)

    def get_by_email(self, *, email: str) -> AuthUser | None:
        """Lookup case-insensitive por email (solo users no borrados)."""
        with db_session() as session:
            return get_user_by_email(session, email.strip().lower())

    def has_password(self, *, user_id: str) -> bool:
        """True si el user tiene credencial password seteada."""
        with db_session() as session:
            return session.get(AuthCredentials, user_id) is not None

    def mfa_summary(self, *, user_id: str) -> dict[str, Any]:
        """Resumen del estado MFA del user (para profile.get + status.get).

        Devuelve `{mfa_configured, mfa_methods, webauthn_count,
        recovery_codes_remaining}`. `count_active_mfa` es transversal
        (mfa_methods + webauthn).
        """
        with db_session() as session:
            total = count_active_mfa(session, user_id=user_id)
            methods = [
                method.kind.value
                for method in list_mfa_methods(session, user_id=user_id)
                if method.confirmed_at is not None
                and method.disabled_at is None
            ]
            webauthn = [
                cred
                for cred in get_webauthn_credentials(session, user_id=user_id)
                if cred.disabled_at is None
            ]
            remaining = count_remaining_recovery_codes(
                session,
                user_id=user_id,
            )
            return {
                'mfa_configured': total > 0,
                'mfa_methods': methods,
                'webauthn_count': len(webauthn),
                'recovery_codes_remaining': remaining,
            }

    def verify_password(self, *, user_id: str, password: str) -> bool:
        """Valida `password` contra el hash argon2 del user.

        False si el user no tiene credencial o la password no matchea.
        """
        with db_session() as session:
            cred = session.get(AuthCredentials, user_id)
            if cred is None:
                return False
            return verify_password(
                password=password,
                hashed=cred.password_hash,
            )

    def update(self, *, user_id: str, **fields: object) -> AuthUser | None:
        """Actualiza un subset de campos del perfil (parcial)."""
        with db_session() as session:
            return update_profile(session, user_id=user_id, **fields)

    def create_email_change_link(
        self,
        *,
        user_id: str,
        new_email: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[str, int]:
        """Genera un magic-link email-change. Devuelve (plain_token, ttl_s).

        El token plano viaja al email NUEVO; en Neon se guarda solo el
        hash + `{new_email}` en metadata.
        """
        plain = generate_opaque_token()
        token_hash = hash_token(plain)
        expires_at = datetime.now(tz=UTC) + _EMAIL_CHANGE_TTL
        with db_session() as session:
            insert_email_change_link(
                session,
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
                new_email=new_email,
                ip=ip,
                user_agent=user_agent,
            )
        return plain, int(_EMAIL_CHANGE_TTL.total_seconds())

    def confirm_email_change(
        self,
        *,
        token: str,
    ) -> tuple[str, str, str] | None:
        """Confirma el cambio de email via el token del magic-link.

        Devuelve `(user_id, old_email, new_email)` si el link es valido y
        el nuevo email sigue libre; None si el link es invalido/expirado/
        consumido. Si el nuevo email ya fue tomado, devuelve None tambien
        (el link queda consumido — el user debe reiniciar el flujo).
        """
        token_hash = hash_token(token)
        with db_session() as session:
            link: AuthMagicLink | None = consume_email_change_link(
                session,
                token_hash=token_hash,
            )
            if link is None:
                return None
            new_email = (link.meta_data or {}).get('new_email')
            if not new_email:
                return None
            # El nuevo email debe seguir libre (otro user pudo registrarlo).
            existing = get_user_by_email(session, new_email)
            if existing is not None and existing.id != link.user_id:
                return None
            user = get_user_by_id(session, user_id=link.user_id)
            if user is None:
                return None
            old_email = user.email
            update_user_email(
                session,
                user_id=link.user_id,
                new_email=new_email,
            )
            return link.user_id, old_email, new_email

    def soft_delete(self, *, user_id: str) -> list[str]:
        """Soft-delete self-service (GDPR). Devuelve las families a blacklistear."""
        anonymized = f'deleted-{user_id}@invalid.local'
        with db_session() as session:
            return soft_delete_user(
                session,
                user_id=user_id,
                anonymized_email=anonymized,
            )

    def hard_delete(self, *, user_id: str) -> bool:
        """Hard-delete (admin only). True si el user existia."""
        with db_session() as session:
            return hard_delete_user(session, user_id=user_id)

    def disable(self, *, user_id: str) -> bool:
        """Marca status=disabled. False si no existe / ya borrado."""
        with db_session() as session:
            return disable_user(session, user_id=user_id)

    def enable(self, *, user_id: str) -> bool:
        """Marca status=active. False si no existe / ya borrado."""
        with db_session() as session:
            return enable_user(session, user_id=user_id)

    def list_paginated(
        self,
        *,
        cursor: str | None = None,
        page_size: int = 50,
        status_filter: str | None = None,
    ) -> list[AuthUser]:
        """Lista users paginado (cursor uuidv7 id ASC)."""
        with db_session() as session:
            return list_users_paginated(
                session,
                cursor=cursor,
                page_size=page_size,
                status_filter=status_filter,
            )

    def admin_detail(self, *, user_id: str) -> dict[str, Any] | None:
        """Detalle de un user para admin.get-user (AC-14/AC-28).

        Devuelve profile (incluye deleted_at + email anonimizado si esta
        soft-deleted) + resumen MFA + count de sesiones + ultimos 10
        eventos de audit. None si el user no existe. NUNCA expone
        password_hash ni el TOTP secret.
        """
        with db_session() as session:
            user = get_user_by_id(session, user_id=user_id)
            if user is None:
                return None
            total = count_active_mfa(session, user_id=user_id)
            methods = [
                method.kind.value
                for method in list_mfa_methods(session, user_id=user_id)
                if method.confirmed_at is not None
                and method.disabled_at is None
            ]
            webauthn = [
                cred
                for cred in get_webauthn_credentials(session, user_id=user_id)
                if cred.disabled_at is None
            ]
            remaining = count_remaining_recovery_codes(
                session,
                user_id=user_id,
            )
            sessions_count = count_user_sessions(session, user_id=user_id)
            recent = list_recent_audit(session, user_id=user_id, limit=10)
            return {
                'profile': {
                    'id': str(user.id),
                    'email': user.email,
                    'display_name': user.display_name,
                    'locale': user.locale,
                    'timezone': user.timezone,
                    'marketing_consent': user.marketing_consent,
                    'status': user.status.value,
                    'created_at': user.created_at.isoformat(),
                    'deleted_at': (
                        user.deleted_at.isoformat()
                        if user.deleted_at is not None
                        else None
                    ),
                    'email_verified_at': (
                        user.email_verified_at.isoformat()
                        if user.email_verified_at is not None
                        else None
                    ),
                    'failed_attempts': user.failed_attempts,
                    'locked_until': (
                        user.locked_until.isoformat()
                        if user.locked_until is not None
                        else None
                    ),
                },
                'mfa': {
                    'mfa_configured': total > 0,
                    'mfa_methods': methods,
                    'webauthn_count': len(webauthn),
                    'recovery_codes_remaining': remaining,
                },
                'sessions_count': sessions_count,
                'recent_audit': [
                    {
                        'event': row.event,
                        'success': row.success,
                        'error_code': row.error_code,
                        'created_at': row.created_at.isoformat(),
                    }
                    for row in recent
                ],
            }
