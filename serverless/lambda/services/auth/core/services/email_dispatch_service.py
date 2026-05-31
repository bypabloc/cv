"""Email dispatch service del Lambda `auth`.

Invoca el Lambda `send_email` de forma asincrona (`InvocationType='Event'`,
fire-and-forget) para enviar el email transaccional (magic-link o code). El
Lambda `send_email` resuelve el template + subject por `kind` desde la tabla
`email-config`, renderiza con Jinja2 y envia via SES.

Reemplaza al patron anterior (publicar a la cola SQS `portfolio-auth-email-
${stage}` consumida por `auth_email_worker`): sin SQS, sin worker. El payload
sigue el contrato de `send_email` (`EmailSendRequest`, `extra='forbid'`):
`{operation:'email', action:'send', data:{kind, to, data, reply_to?}}`.

- `to` es una lista de destinatarios (`send_email` valida `list[str]`).
- `data` lleva SOLO los placeholders Jinja2 que el template del `kind`
  consume — NO `user_id`/`niche`/`subject_id` (el subject sale de
  `email-config`, no del payload). El template de magic-link usa
  `verify_url` + `expires_in_min`; el de code usa `code` + `expires_in_min`.

Best-effort: el invoke async no espera el resultado. Si falla (red/permisos)
se loggea y NO se propaga — el flujo de auth ya completo su parte (el code o
el magic-link ya quedaron persistidos), no se rompe el request por el email.

`user_id` y `niche` se mantienen en las firmas publicas (los callers los
pasan) por compatibilidad, pero NO viajan en el payload del email.
"""

from __future__ import annotations

import os
from typing import Any
from uuid import UUID

from shared.aws.lambda_invoke import LambdaInvokeError, invoke_async
from shared.observability.logger import logger


class EmailDispatchService:
    """Invoca `send_email` async para los emails transaccionales de auth."""

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
        NO viajan en el payload (el template no los usa; `EmailSendRequest`
        forbidea extras top-level). Best-effort: un fallo del invoke se loggea
        y NO se propaga.
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
                'failed to invoke send_email (auth email)',
                extra={'kind': kind, 'user_id': str(user_id)},
            )

    def publish_magic_link(
        self,
        *,
        to: str,
        user_id: UUID | str,
        niche: str | None,
        kind: str,
        verify_url: str,
        expires_in_min: int,
    ) -> None:
        """Invoca `send_email` para un magic-link de register/login/reset.

        `verify_url`: URL completa del magic-link que la plantilla embebe en
        el boton del email. `expires_in_min`: minutos hasta el expiry del
        link (la plantilla lo muestra como "expira en N min").
        """
        self._publish(
            kind=kind,
            to=to,
            user_id=user_id,
            niche=niche,
            data={
                'verify_url': verify_url,
                'expires_in_min': expires_in_min,
            },
        )

    def publish_code(
        self,
        *,
        to: str,
        user_id: UUID | str,
        niche: str | None,
        kind: str,
        code: str,
        expires_in_min: int,
    ) -> None:
        """Invoca `send_email` para un code (8 chars Crockford-like).

        `code`: viaja en claro a `send_email` y al usuario final via email;
        el backend persiste solo el SHA-256. `expires_in_min`: minutos hasta
        el expiry del code.
        """
        self._publish(
            kind=kind,
            to=to,
            user_id=user_id,
            niche=niche,
            data={
                'code': code,
                'expires_in_min': expires_in_min,
            },
        )
