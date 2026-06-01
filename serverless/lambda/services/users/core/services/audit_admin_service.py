"""Audit admin service del Lambda `users`.

Escribe a `auth_user_admin_actions` (audit inmutable de acciones admin).
Cada admin operation (disable/enable/force-logout/delete) inserta un row
ANTES de la accion destructiva (audit pre-hoc). Tambien registra los
intentos de acceso admin (`log_attempt`, exitosos y fallidos).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from shared.db.repositories.auth_users import (
    insert_admin_action,
    list_admin_actions,
)
from shared.db.session import db_session


class AuditAdminService:
    """Wrapper de `insert_admin_action` + `list_admin_actions`."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def log(
        self,
        *,
        admin_user_id: UUID | str | None,
        target_user_id: UUID | str | None,
        action: str,
        meta_data: dict[str, Any] | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Inserta un row de audit admin."""
        with db_session() as session:
            insert_admin_action(
                session,
                admin_user_id=(
                    str(admin_user_id) if admin_user_id is not None else None
                ),
                target_user_id=(
                    str(target_user_id) if target_user_id is not None else None
                ),
                action=action,
                meta_data=meta_data,
                ip=ip,
                user_agent=user_agent,
            )

    def log_attempt(
        self,
        *,
        admin_user_id: UUID | str | None,
        action: str,
        success: bool,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Registra un intento de acceso admin (success o no)."""
        self.log(
            admin_user_id=admin_user_id,
            target_user_id=None,
            action=action,
            meta_data={'success': success},
            ip=ip,
            user_agent=user_agent,
        )

    def list_actions(
        self,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page_size: int = 50,
        cursor: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lista admin actions (created_at DESC, paginado por id)."""
        with db_session() as session:
            rows = list_admin_actions(
                session,
                from_date=from_date,
                to_date=to_date,
                page_size=page_size,
                cursor=cursor,
            )
            return [
                {
                    'id': str(row.id),
                    'admin_user_id': (
                        str(row.admin_user_id)
                        if row.admin_user_id is not None
                        else None
                    ),
                    'target_user_id': (
                        str(row.target_user_id)
                        if row.target_user_id is not None
                        else None
                    ),
                    'action': row.action,
                    'metadata': row.meta_data,
                    # row.ip es INET -> psycopg3 lo devuelve como
                    # ipaddress.IPv4Address/IPv6Address, NO serializable a
                    # JSON. str() lo normaliza; None se preserva.
                    'ip': str(row.ip) if row.ip is not None else None,
                    'created_at': row.created_at.isoformat(),
                }
                for row in rows
            ]
