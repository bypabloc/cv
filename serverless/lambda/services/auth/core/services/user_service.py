"""User service del Lambda `auth`.

Encapsula las operaciones de alto nivel sobre `auth_users`:
- `get_by_email(email)`: lookup case-insensitive (CITEXT).
- `create_pending(email)`: crea row con status='pending'.
- `mark_active(user)`: marca activo + reset failed_attempts.
- `increment_failed_attempts(user)`: +1 al contador. Si >= 5, llama
  internamente a `lock_user` con 15 min de bloqueo (politica MVP).
- `reset_failed_attempts(user)`: tras login exitoso.
- `lock_user(user, until)`: status='locked' + locked_until.

Las queries puras viven en `shared.db.repositories.auth`; este service
las orquesta y aporta la regla de auto-lock al 5to fallo.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from shared.db import db_session
from shared.db.models import AuthCodeKind, AuthLinkKind, AuthUser
from shared.db.repositories.auth import (
    create_pending_user,
    get_user_by_email,
    increment_failed_attempts,
    invalidate_active_codes_and_links,
    lock_user,
    mark_user_active,
    reset_failed_attempts,
    set_password_hash,
    update_last_login,
)

# Politica MVP: 15 min de bloqueo tras 5 fallos consecutivos.
_LOCK_DURATION = timedelta(minutes=15)
_MAX_FAILED_ATTEMPTS = 5


class UserService:
    """Service de auth_users (lookup + create + lock/unlock)."""

    def __init__(self, app_config: object) -> None:
        """`app_config` se acepta por uniformidad (no se usa hoy)."""
        self.app_config = app_config

    def get_by_email(self, email: str) -> AuthUser | None:
        """Lookup case-insensitive del user por email. None si no existe."""
        with db_session() as session:
            return get_user_by_email(session, email.strip().lower())

    def get_by_id(self, user_id: str) -> AuthUser | None:
        """Lookup por UUID. None si no existe."""
        with db_session() as session:
            return session.get(AuthUser, user_id)

    def create_pending(self, *, email: str) -> AuthUser:
        """Crea un user nuevo con status='pending'."""
        with db_session() as session:
            return create_pending_user(session, email=email.strip().lower())

    def mark_active(self, user: AuthUser) -> None:
        """Cambia status a active + setea email_verified_at."""
        with db_session() as session:
            session.add(user)
            mark_user_active(session, user)

    def increment_failed_attempts(self, user: AuthUser) -> int:
        """Incrementa el contador y, al 5to fallo, lockea 15 min.

        Retorna el contador nuevo.
        """
        with db_session() as session:
            session.add(user)
            attempts = increment_failed_attempts(session, user)
            if attempts >= _MAX_FAILED_ATTEMPTS:
                until = datetime.now(tz=UTC) + _LOCK_DURATION
                lock_user(session, user, until=until)
            return attempts

    def reset_failed_attempts(self, user: AuthUser) -> None:
        """Resetea el contador (post-login exitoso)."""
        with db_session() as session:
            session.add(user)
            reset_failed_attempts(session, user)

    def lock_user(self, user: AuthUser, *, until: datetime) -> None:
        """Lockea manualmente al user hasta el datetime dado."""
        with db_session() as session:
            session.add(user)
            lock_user(session, user, until=until)

    def set_password_hash(
        self,
        *,
        user_id: str,
        password_hash: str,
        algo: str = 'argon2id',
    ) -> None:
        """Upsert del password_hash del user (AC-4).

        Delega al repository `shared.db.repositories.auth.set_password_hash`
        que upserta el row en `auth_credentials` (1-to-0..1 con `auth_users`).
        Lo invoca el controller `verify.set-password` tras validar el
        rolling temp JWT del flujo y antes de emitir access+refresh.
        """
        with db_session() as session:
            set_password_hash(
                session,
                user_id=user_id,
                password_hash=password_hash,
                algo=algo,
            )

    def update_last_login(self, user: AuthUser) -> None:
        """Setea last_login_at=now + resetea failed_attempts (AC-22).

        Lo llaman los controllers `login/verify_magic_link` y
        `login/verify_code` tras un login exitoso.
        """
        with db_session() as session:
            session.add(user)
            update_last_login(session, user)

    def invalidate_active_codes_and_links(
        self,
        *,
        user_id: str,
        kind_code: AuthCodeKind = AuthCodeKind.REGISTER,
        kind_link: AuthLinkKind = AuthLinkKind.REGISTER,
    ) -> None:
        """Invalida codes + magic_links activos del user (AC-19).

        Usado por `register.start` cuando el visitante reinicia el flow.
        """
        with db_session() as session:
            invalidate_active_codes_and_links(
                session,
                user_id=user_id,
                kind_code=kind_code,
                kind_link=kind_link,
            )
