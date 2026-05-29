"""Session service del Lambda `users`.

CRUD de lectura/revocacion sobre `auth_user_sessions` (las sesiones las
INSERTA el Lambda `auth` via su session_tracking_service). Lista las
sesiones del user, revoca una individual (y devuelve su family_id para que
el controller la blackliste) y revoca todas (force-logout / delete).
"""

from __future__ import annotations

from typing import Any

from shared.db import db_session
from shared.db.repositories.auth_users import (
    get_session_by_id,
    list_user_sessions,
    revoke_all_user_sessions,
    revoke_session,
)


def _device_summary(device_info: dict[str, Any] | None) -> dict[str, Any]:
    """Normaliza device_info a un dict serializable (vacio si None)."""
    return device_info or {}


class SessionService:
    """Service de auth_user_sessions (list + revoke)."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def list_for_user(
        self, *, user_id: str, current_family_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lista las sesiones activas, last_active_at DESC.

        Marca `current: true` la sesion cuyo `family_id` coincide con el
        del access JWT en curso (`current_family_id`).
        """
        with db_session() as session:
            rows = list_user_sessions(session, user_id=user_id)
            return [
                {
                    'session_id': str(row.id),
                    'device_info': _device_summary(row.device_info),
                    'ip': row.ip,
                    'country': row.country,
                    'created_at': row.created_at.isoformat(),
                    'last_active_at': row.last_active_at.isoformat(),
                    'current': (
                        current_family_id is not None
                        and row.family_id == current_family_id
                    ),
                }
                for row in rows
            ]

    def get_family(self, *, user_id: str, session_id: str) -> str | None:
        """Devuelve el family_id de una sesion del user (dual filter), o None
        si no existe / no es del user. Lo usa `revoke-session` para saber si
        la sesion objetivo es la actual (AC-10)."""
        with db_session() as session:
            row = get_session_by_id(
                session, user_id=user_id, session_id=session_id,
            )
            return row.family_id if row is not None else None

    def revoke_session(self, *, user_id: str, session_id: str) -> str | None:
        """Borra una sesion del user. Devuelve su family_id (para blacklist)
        o None si no existe / no es del user."""
        with db_session() as session:
            return revoke_session(
                session, user_id=user_id, session_id=session_id,
            )

    def revoke_all_for_user(self, *, user_id: str) -> list[str]:
        """Borra TODAS las sesiones del user. Devuelve los family_id borrados."""
        with db_session() as session:
            return revoke_all_user_sessions(session, user_id=user_id)
