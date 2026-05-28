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
from shared.db.models import AuthUser
from shared.db.repositories.auth import (
    create_pending_user,
    get_user_by_email,
    increment_failed_attempts,
    lock_user,
    mark_user_active,
    reset_failed_attempts,
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
