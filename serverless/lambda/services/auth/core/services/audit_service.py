"""Audit service del Lambda `auth`.

Inserta un row en `auth_audit_log` por cada evento de auth observable
(register.start, login.start, verify.set-password, session.refresh,
session.logout, ...). Es insert-only — nadie modifica los rows.

Eventos canonicos: `<operation>.<action>`. `success=False` solo cuando
el flujo falla por motivo de negocio (EMAIL_NOT_FOUND,
INVALID_CODE, ...); errores 5xx no necesariamente quedan en este log
(viven en CloudWatch).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from shared.db.repositories.auth import insert_audit_event
from shared.db.session import db_session
from shared.observability.logger import logger


class AuditService:
    """Wrapper de `insert_audit_event` con la signature del dominio."""

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
        """Inserta un row de auditoria. NO propaga si Neon falla.

        Best-effort: si Neon falla (rollback, DB caida, tabla inexistente),
        la excepcion se SWALLOWea aqui (logger.exception) para no romper el
        flujo principal de auth — el audit es metadata, no parte del camino
        critico. Sin este try/except un fallo de Neon convertiria un login
        exitoso en un 500.
        """
        try:
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
        except Exception:
            logger.exception(
                'audit log insert failed (best-effort)',
                extra={'event': event},
            )
