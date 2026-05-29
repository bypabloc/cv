"""Session service: revocacion global de sesiones por user (AC-27).

`revoke_all_for_user` setea `auth_users.sessions_revoked_at = now()`.
`session.refresh` rechaza (401 TOKEN_FAMILY_REVOKED) cualquier refresh
JWT cuyo `iat` sea anterior a ese timestamp. Lo invoca el side-effect de
confirmar el PRIMER metodo MFA del user (transicion 0 -> 1): cierra la
ventana donde un atacante con un refresh previo seguiria operando sin
pasar MFA (decision 15 del plan 02).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from shared.db import db_session
from shared.db.models import AuthUser


class SessionService:
    """Revocacion de sesiones a nivel de user (epoch en auth_users)."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def revoke_all_for_user(self, *, user_id: UUID | str) -> None:
        """Setea el epoch de revocacion del user a now() (AC-27)."""
        with db_session() as session:
            user = session.get(AuthUser, str(user_id))
            if user is not None:
                user.sessions_revoked_at = datetime.now(tz=UTC)
                session.flush()
