"""@module models.email — validacion del evento del Lambda send_email.

`EmailSendRequest` valida el `data` del evento
`{operation:'email', action:'send', data}`. Hereda de `BaseModel`
(shared.core) con `extra='forbid'`.
"""

from __future__ import annotations

from typing import Any

from shared.core.pydantic_types import BaseModel, ConfigDict, Field


class EmailSendRequest(BaseModel):
    """Valida el `data` del request de envio de email.

    - kind: clave en la tabla `email-config` (template + subject).
    - to: destinatarios. Para `contact` los pasa contact_form (owner);
      para auth/users el email del user.
    - data: variables del template (contexto Jinja2). Default {}.
    - reply_to: opcional; solo `contact` lo usa (email del visitante).
    """

    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    kind: str = Field(min_length=1)
    to: list[str] = Field(min_length=1)
    data: dict[str, Any] = Field(default_factory=dict)
    reply_to: list[str] | None = Field(default=None)
