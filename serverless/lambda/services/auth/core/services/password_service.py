"""Password service: estado de la password del user (overview de seguridad).

Solo lectura: `status` resuelve `auth_credentials` (1-to-0..1 con
`auth_users`) para el overview de la operation `security`. Devuelve
primitivos serializables, NUNCA el hash de la password.
"""

from __future__ import annotations

from uuid import UUID

from shared.db.repositories.auth_users import get_password_status
from shared.db.session import db_session


class PasswordService:
    """Estado de la password del user (`auth_credentials`)."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def status(self, *, user_id: UUID | str) -> dict[str, object | None]:
        """`{has_password, last_change_at}` (ISO 8601 o None)."""
        with db_session() as session:
            return get_password_status(session, user_id=str(user_id))
