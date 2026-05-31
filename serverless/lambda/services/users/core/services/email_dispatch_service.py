"""Email dispatch service del Lambda `users`.

Invoca el Lambda `send_email` de forma asincrona (`InvocationType='Event'`,
fire-and-forget) para las notificaciones del dominio gestion de usuarios.
`send_email` resuelve template + subject por `kind` desde `email-config`,
renderiza con Jinja2 y envia via SES.

Reemplaza al patron anterior (publicar a la cola SQS consumida por
`auth_email_worker`): sin SQS, sin worker. El payload sigue el contrato de
`send_email` (`EmailSendRequest`, `extra='forbid'`):
`{operation:'email', action:'send', data:{kind, to, data}}` — `to` es una
lista y `data` lleva SOLO los placeholders Jinja2 del template (NO
`user_id`/`niche`/`subject_id`).

Los 4 kinds del plan 03: `email-change-verify` (magic-link al email NUEVO),
`email-changed` (notif al viejo), `account-disabled`, `account-deleted`.

Best-effort: un fallo del invoke se loggea y NO se propaga. `user_id`/`niche`
se mantienen en las firmas publicas por compatibilidad con los callers pero
NO viajan en el payload del email.
"""

from __future__ import annotations

import os
from typing import Any
from uuid import UUID

from shared.aws.lambda_invoke import LambdaInvokeError, invoke_async
from shared.observability.logger import logger


class EmailDispatchService:
    """Invoca `send_email` async para las notificaciones del Lambda `users`."""

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
    ) -> None:
        """Invoca `send_email` async con el contrato `EmailSendRequest`.

        `user_id`/`niche` se aceptan por compatibilidad con los callers pero
        NO viajan en el payload. Best-effort: un fallo del invoke se loggea y
        NO se propaga.
        """
        function_name = os.environ['LAMBDA_SEND_EMAIL_FUNCTION_NAME']
        payload = {
            'operation': 'email',
            'action': 'send',
            'data': {
                'kind': kind,
                'to': [to],
                'data': data,
            },
        }
        try:
            invoke_async(function_name=function_name, payload=payload)
        except LambdaInvokeError:
            logger.exception(
                'failed to invoke send_email (users notification)',
                extra={'kind': kind, 'user_id': str(user_id)},
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
    ) -> None:
        """Magic-link de confirmacion al email NUEVO (kind email-change-verify)."""
        self._publish(
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
    ) -> None:
        """Notificacion al email VIEJO de que el email se cambio."""
        self._publish(
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
    ) -> None:
        """Notificacion al user de que su cuenta fue deshabilitada."""
        self._publish(
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
    ) -> None:
        """Notificacion al user de que su cuenta fue eliminada."""
        self._publish(
            kind='account-deleted',
            to=to,
            user_id=user_id,
            niche=niche,
            data={},
        )
