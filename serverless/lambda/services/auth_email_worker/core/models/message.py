"""@module message — esquema del mensaje SQS del worker auth_email_worker.

El productor (Lambda `auth`) publica un mensaje JSON con este shape en
la cola `portfolio-auth-email-${stage}`. Este modelo lo valida en el
worker como parte del ciclo del controller (`validate` phase).

Campos del mensaje:

- `kind`: discriminador del tipo de email (5 valores).
- `to`: destinatario (string email valido).
- `user_id`: UUID del usuario en `auth_users` (para el audit log).
- `niche`: nicho de origen opcional (para audit + plantillas niche-aware).
- `subject_id`: clave logica del subject (ej. `auth.register.magic-link.subject`).
- `data`: dict libre con los placeholders del template
  (`token`/`code`/`verify_url`/`expires_in_min` segun el kind).
- `audit_event_id`: id opcional del evento previo (correlation con el
  audit log que genero el envio).
"""

from typing import Any, Literal
from uuid import UUID

from shared.core import BaseModel, ConfigDict, EmailStr, Field

# Discriminador de tipos de email que el worker sabe enviar. Mantener
# alineado con `template_service.SUPPORTED_KINDS`.
#
# Plan 03 (gestion de usuarios) agrega 4 kinds: `email-change-verify`
# (magic-link al email NUEVO para confirmar el cambio), `email-changed`
# (notificacion al email VIEJO de que se cambio), `account-disabled` y
# `account-deleted` (notificaciones del estado de la cuenta).
AuthEmailKind = Literal[
    'register-magic-link',
    'register-code',
    'login-magic-link',
    'login-code',
    'password-reset',
    'email-change-verify',
    'email-changed',
    'account-disabled',
    'account-deleted',
]


class AuthEmailMessage(BaseModel):
    """Mensaje SQS que la Lambda `auth` encola al worker.

    Contrato del payload (lo que el productor pone en `record['body']`
    serializado como JSON). El handler hace `json.loads(body)` y se lo
    pasa al controller como `data`; el controller lo valida con este
    modelo.

    `extra='forbid'` rechaza campos no declarados (mensajes malformados
    o de schema_version distinta van al batchItemFailures y luego a la
    DLQ).
    """

    model_config = ConfigDict(extra='forbid')

    # Discriminador: el worker selecciona la plantilla por `kind`.
    kind: AuthEmailKind

    # Destinatario y referencia al usuario en Neon.
    to: EmailStr
    user_id: UUID

    # Nicho de origen (opcional). El plan permite plantillas niche-aware
    # en el futuro; hoy solo se usa para auditoria.
    niche: str | None = None

    # Clave logica del subject (para i18n centralizado, hoy solo log).
    subject_id: str = Field(..., min_length=1, max_length=128)

    # Datos del template: `token` / `code` / `verify_url` /
    # `expires_in_min`. Schema libre por diseño: cada `kind` consume las
    # claves que necesita, no se valida mas estricto aqui (el template
    # falla si falta una clave requerida).
    data: dict[str, Any] = Field(default_factory=dict)

    # Correlation con el audit log original (opcional).
    audit_event_id: str | None = None
