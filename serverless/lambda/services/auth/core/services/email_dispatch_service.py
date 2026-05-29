"""Email dispatch service del Lambda `auth`.

Publica mensajes a la cola `portfolio-auth-email-${stage}` que consume
el `auth_email_worker`. El worker renderiza la plantilla por `kind`,
envia el email via SES y registra `email.sent.<kind>` en `auth_audit_log`.

El payload sigue EXACTAMENTE el shape que valida el worker
(`AuthEmailMessage`, ver `auth_email_worker/core/models/message.py`):
`{kind, to, user_id, niche, subject_id, data}` — con `subject_id` y SIN
`schema_version`/`locale`. El modelo del worker tiene `extra='forbid'`,
asi que cualquier campo extra (o un `subject_id` ausente) hace fallar la
validacion y el mensaje termina en la DLQ sin enviarse. NO importamos ese
modelo aqui para mantener la independencia de deploy entre los dos
Lambdas: el shape se mantiene compatible via tests.

`data` lleva los placeholders que la plantilla del `kind` consume:
- magic-link (`register-magic-link`, `login-magic-link`, `password-reset`):
  `verify_url` + `expires_in_min`.
- code (`register-code`, `login-code`): `code` + `expires_in_min`.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from shared.queue.publisher import send_to_queue


def _subject_id(kind: str) -> str:
    """Clave logica del subject que el worker loggea en el audit.

    El subject real del email lo resuelve el worker por `kind` desde su
    `_SUBJECTS_ES`; aqui solo damos una clave estable y no vacia (el modelo
    exige `min_length=1`).
    """
    return f'auth.{kind}.subject'


class EmailDispatchService:
    """Publisher de mensajes hacia el `auth_email_worker` via SQS."""

    # Short name del catalogo de colas (mismo que el resolver SSM espera:
    # 'auth-email' -> SSM_AUTH_EMAIL_QUEUE_URL_PATH).
    _QUEUE_SHORT_NAME = 'auth-email'

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
        """Arma el payload con el shape de `AuthEmailMessage` y lo encola."""
        payload: dict[str, Any] = {
            'kind': kind,
            'to': to,
            'user_id': str(user_id),
            'niche': niche,
            'subject_id': _subject_id(kind),
            'data': data,
        }
        return send_to_queue(
            queue_short_name=self._QUEUE_SHORT_NAME,
            payload=payload,
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
    ) -> str:
        """Publica un mensaje de magic-link al worker.

        `verify_url`: URL completa del magic-link que la plantilla embebe en
        el boton del email. `expires_in_min`: minutos hasta el expiry del
        link (la plantilla lo muestra como "expira en N min").
        """
        return self._publish(
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
    ) -> str:
        """Publica un mensaje de code (8 chars Crockford-like) al worker.

        `code`: viaja en claro al worker y al usuario final via email; el
        backend persiste solo el SHA-256. `expires_in_min`: minutos hasta
        el expiry del code.
        """
        return self._publish(
            kind=kind,
            to=to,
            user_id=user_id,
            niche=niche,
            data={
                'code': code,
                'expires_in_min': expires_in_min,
            },
        )
