"""Email dispatch service del Lambda `users`.

Publica mensajes a la cola `portfolio-auth-email-${stage}` que consume el
`auth_email_worker`. El payload sigue EXACTAMENTE el shape que valida el
worker (`AuthEmailMessage`): `{kind, to, user_id, niche, subject_id,
data}` — con `subject_id` y SIN `schema_version`/`locale` (el modelo del
worker tiene `extra='forbid'`). NUNCA invoca SES directo.

Los 4 kinds del plan 03: `email-change-verify` (magic-link al email
NUEVO), `email-changed` (notif al viejo), `account-disabled`,
`account-deleted`.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from shared.queue.publisher import send_to_queue

_QUEUE_SHORT_NAME = 'auth-email'


def _subject_id(kind: str) -> str:
    """Clave logica del subject (el worker la loggea; el subject real sale
    de su _SUBJECTS_ES)."""
    return f'auth.users.{kind}.subject'


class EmailDispatchService:
    """Publisher de notificaciones hacia el `auth_email_worker` via SQS."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def _publish(
        self,
        *,
        kind: str,
        to: str,
        user_id: UUID | str,
        niche: str | None,
        data: dict[str, Any],
    ) -> str:
        payload: dict[str, Any] = {
            'kind': kind,
            'to': to,
            'user_id': str(user_id),
            'niche': niche,
            'subject_id': _subject_id(kind),
            'data': data,
        }
        return send_to_queue(
            queue_short_name=_QUEUE_SHORT_NAME,
            payload=payload,
        )

    def publish_email_change_verify(
        self,
        *,
        to: str,
        user_id: UUID | str,
        niche: str | None,
        new_email: str,
        verify_url: str,
        expires_in_min: int,
    ) -> str:
        """Magic-link de confirmacion al email NUEVO (kind email-change-verify)."""
        return self._publish(
            kind='email-change-verify',
            to=to,
            user_id=user_id,
            niche=niche,
            data={
                'new_email': new_email,
                'verify_url': verify_url,
                'expires_in_min': expires_in_min,
            },
        )

    def publish_email_changed(
        self,
        *,
        to: str,
        user_id: UUID | str,
        niche: str | None,
        new_email: str,
    ) -> str:
        """Notificacion al email VIEJO de que el email se cambio."""
        return self._publish(
            kind='email-changed',
            to=to,
            user_id=user_id,
            niche=niche,
            data={'new_email': new_email},
        )

    def publish_account_disabled(
        self,
        *,
        to: str,
        user_id: UUID | str,
        niche: str | None,
        reason: str,
    ) -> str:
        """Notificacion al user de que su cuenta fue deshabilitada."""
        return self._publish(
            kind='account-disabled',
            to=to,
            user_id=user_id,
            niche=niche,
            data={'reason': reason},
        )

    def publish_account_deleted(
        self,
        *,
        to: str,
        user_id: UUID | str,
        niche: str | None,
    ) -> str:
        """Notificacion al user de que su cuenta fue eliminada."""
        return self._publish(
            kind='account-deleted',
            to=to,
            user_id=user_id,
            niche=niche,
            data={},
        )
