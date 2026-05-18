"""Pydantic schemas para tracking pixel."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# Tamano maximo del event_props serializado a JSON. event_props es un dict
# libre con datos especificos por tipo de evento (href del link, scroll %,
# campo del form). 2 KB acota el volumen y evita payloads abusivos.
EVENT_PROPS_MAX_BYTES = 2048


class TrackingEventInput(BaseModel):
    """Body schema POST /track."""

    # Session: cliente genera UUID4 en localStorage al primer visit
    session_id: str = Field(..., min_length=20, max_length=64)

    # Identificador del evento: UUIDv4 generado por el cliente, uno por
    # evento. Sirve de idempotencia ante reintentos de sendBeacon.
    event_id: str = Field(..., min_length=32, max_length=36)

    # Tipo de evento: UUID del catalogo event_types (FK). Requerido: todo
    # evento debe estar tipado (page_load, etc.).
    event_type_id: str = Field(..., min_length=36, max_length=36)

    # Page metadata (cliente lo provee)
    page_url: str = Field(..., max_length=500)
    page_title: str | None = Field(default=None, max_length=200)
    page_path: str | None = Field(default=None, max_length=300)
    referrer: str | None = Field(default=None, max_length=500)

    # UTM params (campaign tracking)
    utm_source: str | None = Field(default=None, max_length=100)
    utm_medium: str | None = Field(default=None, max_length=100)
    utm_campaign: str | None = Field(default=None, max_length=100)
    utm_content: str | None = Field(default=None, max_length=100)
    utm_term: str | None = Field(default=None, max_length=100)

    # Viewport (cliente lo manda)
    viewport_width: int | None = Field(default=None, ge=0, le=10000)
    viewport_height: int | None = Field(default=None, ge=0, le=10000)

    # Niche (que subdominio)
    niche: str | None = Field(default=None, max_length=50)

    # Opcional: cf_token de Turnstile invisible (best-effort, no enforced)
    cf_token: str | None = Field(default=None, max_length=2048)

    # Datos especificos por tipo de evento (SPEC-200): href del link
    # clickeado, profundidad de scroll, campo del form, codigo de error.
    # Dict libre acotado en tamano; se replica a la columna jsonb de Neon.
    event_props: dict[str, Any] | None = Field(default=None)

    @field_validator('event_props')
    @classmethod
    def validate_event_props_size(
        cls, v: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """
        Valida que event_props serializado a JSON no exceda el limite.

        event_props es un dict libre; un payload abusivo inflaria el item de
        DynamoDB y la fila de Neon. Se serializa a JSON y se mide en bytes.
        Si excede EVENT_PROPS_MAX_BYTES, lanza ValueError que Pydantic
        convierte en ValidationError -> el handler responde 400 INVALID_INPUT.
        """
        if v is None:
            return None
        serialized = json.dumps(v, separators=(',', ':'))
        size = len(serialized.encode('utf-8'))
        if size > EVENT_PROPS_MAX_BYTES:
            msg = (
                f'event_props excede el tamano maximo '
                f'({size} > {EVENT_PROPS_MAX_BYTES} bytes)'
            )
            raise ValueError(msg)
        return v

    @field_validator('event_id', 'event_type_id')
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """
        Valida que el valor sea un UUID bien formado.

        El cliente puede enviar el UUID con o sin guiones (`event_id` se
        genera con `crypto.randomUUID()` y a veces se compacta). Se acepta
        cualquiera de las dos formas y se devuelve el string original;
        `UUID()` lanza ValueError si el formato es invalido, que Pydantic
        convierte en ValidationError -> 400 INVALID_INPUT.
        """
        UUID(v)
        return v
