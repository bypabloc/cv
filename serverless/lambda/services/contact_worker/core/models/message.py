"""@module message — esquema del mensaje SQS del worker contact_worker.

El encoder (Lambda `contact_form`) publica un mensaje JSON con este shape
en la cola `portfolio-contact-form-${stage}`. Este modelo lo valida en el
worker como parte del ciclo del controller (`validate` phase).

Schema versionado: si la forma del mensaje cambia, bump `schema_version`
y el worker soporta multiples versiones por compatibilidad backward
durante el rollout (encoders nuevos publican v2 mientras workers viejos
siguen procesando v1). En esta version solo existe v1.
"""

from datetime import datetime
from typing import Literal

from shared.core.pydantic_types import BaseModel, ConfigDict, EmailStr, Field


class ContactQueueMessage(BaseModel):
    """Mensaje SQS que la Lambda `contact_form` encola al worker.

    Contrato del payload (lo que el encoder pone en `record['body']`
    serializado como JSON). El handler hace `json.loads(body)` y se lo
    pasa al controller como `data`; el controller lo valida con este
    modelo.

    `extra='forbid'` rechaza campos no declarados (mensajes malformados
    o de schema_version distinta van al batchItemFailures y luego a la
    DLQ, evitando que un cambio silencioso en el encoder corrompa la
    persistencia).
    """

    model_config = ConfigDict(extra='forbid')

    # Version del schema del mensaje. Permite branchear por version en
    # rollouts. Por ahora solo existe v1.
    schema_version: Literal[1] = 1

    # IDs pre-generados por el encoder. El worker NO los regenera (clave
    # para la idempotencia: si SQS re-entrega el mismo mensaje, el
    # contact_id es el mismo y el INSERT con ON CONFLICT DO NOTHING es
    # no-op).
    contact_id: str = Field(..., min_length=36, max_length=36)  # UUIDv7
    created_at: datetime
    session_id: str = Field(..., min_length=1, max_length=128)

    # Campos del form (ya validados/sanitizados por el encoder).
    name: str
    email: EmailStr
    message: str
    company: str | None = None
    role: str | None = None
    service_type: str | None = None
    budget: str | None = None
    timeline: str | None = None
    niche: str | None = None

    # Metadata HTTP del request original (para
    # `ensure_session_and_visit`). El worker NUNCA recibe `cf_token` ni
    # `bypass_secret`: el encoder ya valido Turnstile.
    ip: str
    country: str | None = None
    user_agent: str | None = None
    origin_niche: str | None = None
