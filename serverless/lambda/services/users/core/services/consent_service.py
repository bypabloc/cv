"""Consent service del Lambda `users`.

Escribe a `auth_user_consent_log` (log GDPR de cambios de consentimiento).
Lo usa `profile.update` cuando `marketing_consent` (o
`privacy_policy_version`) cambia de valor.
"""

from __future__ import annotations

from shared.db import db_session
from shared.db.repositories.auth_users import insert_consent_log


class ConsentService:
    """Wrapper de `insert_consent_log`."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def log(
        self,
        *,
        user_id: str,
        field: str,
        old_value: str | None,
        new_value: str | None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Inserta un row de consent log."""
        with db_session() as session:
            insert_consent_log(
                session,
                user_id=user_id,
                field=field,
                old_value=old_value,
                new_value=new_value,
                ip=ip,
                user_agent=user_agent,
            )
