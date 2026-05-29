"""Audit service generico del Lambda `users`.

Escribe eventos a `auth_audit_log` (mismo que el Lambda `auth`) via el
repo `shared.db.repositories.auth.insert_audit_event`. Lo usan los
controllers de profile/status para dejar traza de cada operacion.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from shared.db import db_session
from shared.db.repositories.auth import insert_audit_event


class AuditService:
    """Wrapper de `insert_audit_event` (event naming `<operation>.<action>`)."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def log(
        self,
        *,
        event: str,
        success: bool,
        user_id: UUID | str | None = None,
        error_code: str | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
        niche: str | None = None,
        meta_data: dict[str, Any] | None = None,
    ) -> None:
        """Inserta un row en auth_audit_log."""
        with db_session() as session:
            insert_audit_event(
                session,
                event=event,
                success=success,
                user_id=str(user_id) if user_id is not None else None,
                error_code=error_code,
                ip=ip,
                user_agent=user_agent,
                niche=niche,
                meta_data=meta_data,
            )
