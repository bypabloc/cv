"""@module audit_service — inserta filas en `auth_audit_log`.

Wrapper sobre `shared.db.repositories.auth.insert_audit_event` que abre
un `db_session()` (transaccion auto-commit) por cada evento. Si el
INSERT falla, propaga la excepcion: el handler lo capturara y SQS
reintentara el mensaje completo (trade-off: el email puede ir 2 veces,
pero NUNCA perdemos la auditoria).
"""

from __future__ import annotations

from typing import Any

from shared.db import db_session
from shared.db.repositories.auth import insert_audit_event
from shared.observability.logger import logger

__all__ = ['log_email_audit']


def log_email_audit(
    *,
    event: str,
    success: bool,
    user_id: str | None = None,
    error_code: str | None = None,
    niche: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    """Registra un evento en `auth_audit_log`.

    Parameters
    ----------
    event : str
        Nombre del evento (`email.sent.<kind>` o
        `email.send.failed.<kind>`).
    success : bool
        True si el envio fue exitoso.
    user_id : str | None
        UUID del usuario (en `auth_users`).
    error_code : str | None
        Codigo de error logico si `success=False`.
    niche : str | None
        Nicho de origen del flujo.
    meta : dict | None
        Metadata adicional (subject_id, message_id, reason, ...).
    """
    with db_session() as session:
        insert_audit_event(
            session,
            event=event,
            success=success,
            user_id=user_id,
            error_code=error_code,
            niche=niche,
            meta_data=meta,
        )

    logger.info(
        'auth audit event recorded',
        extra={
            'event': event,
            'success': success,
            'user_id': user_id,
        },
    )
