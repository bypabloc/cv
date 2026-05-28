"""Email dispatch service del Lambda `auth`.

Publica mensajes a la cola `portfolio-auth-email-${stage}` que consume
el `auth_email_worker`. El worker renderiza la plantilla por `kind` +
locale, envia el email via SES y registra el `email.sent.<kind>` en
`auth_audit_log`.

El payload publicado sigue el shape esperado por el worker (ver
`auth_email_worker/core/models/message.py`). Aqui NO importamos ese
modelo para mantener la independencia de deploy entre los dos
Lambdas: el shape se mantiene compatible via tests.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from shared.queue import send_to_queue


class EmailDispatchService:
    """Publisher de mensajes hacia el `auth_email_worker` via SQS."""

    # Short name del catalogo de colas (mismo que el resolver SSM espera:
    # 'auth-email' -> SSM_AUTH_EMAIL_QUEUE_URL_PATH).
    _QUEUE_SHORT_NAME = 'auth-email'

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def publish_magic_link(
        self,
        *,
        to: str,
        user_id: UUID | str,
        niche: str | None,
        kind: str,
        plain: str,
        verify_url: str,
    ) -> str:
        """Publica un mensaje `kind=magic-link` al worker.

        `plain`: token opaco que el worker embebe en el HTML del email.
        `verify_url`: URL completa del magic-link (api/auth?... &token=<plain>).
        """
        payload: dict[str, Any] = {
            'schema_version': 1,
            'kind': kind,
            'to': to,
            'user_id': str(user_id),
            'niche': niche,
            'locale': 'es',
            'data': {
                'token': plain,
                'verify_url': verify_url,
            },
        }
        return send_to_queue(
            queue_short_name=self._QUEUE_SHORT_NAME,
            payload=payload,
        )

    def publish_code(
        self,
        *,
        to: str,
        user_id: UUID | str,
        niche: str | None,
        kind: str,
        code: str,
    ) -> str:
        """Publica un mensaje `kind=code` al worker.

        `code`: 8 chars Crockford-like. Viaja en claro al worker y al
        usuario final via email; el backend persiste solo el SHA-256.
        """
        payload: dict[str, Any] = {
            'schema_version': 1,
            'kind': kind,
            'to': to,
            'user_id': str(user_id),
            'niche': niche,
            'locale': 'es',
            'data': {
                'code': code,
            },
        }
        return send_to_queue(
            queue_short_name=self._QUEUE_SHORT_NAME,
            payload=payload,
        )
