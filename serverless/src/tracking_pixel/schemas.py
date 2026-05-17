"""Pydantic schemas para tracking pixel."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


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
