"""Modelos Pydantic de la operacion `tracking`.

`TrackEventModel` valida el campo `data` del evento sintetico que el
handler construye desde el evento HTTP de API Gateway (`POST /track`).

El `data` del evento sintetico es el body JSON del POST mas una clave
`meta` (TrackEventMeta) con la IP, el country y el User-Agent que el
handler extrae de la request HTTP. Se enrutan via el modelo (en vez de
un canal aparte) para que el controller reciba TODO el contexto que
necesita en un solo objeto validado, sin conocer el evento Lambda crudo.

Decision de diseno: `meta` es un campo Pydantic mas (no un atributo
privado). El handler arma `data = {**body, 'meta': {...}}` y el modelo
lo valida junto al resto del payload. Asi el controller obtiene IP /
country / User-Agent ya validados, sin tocar el evento Lambda crudo y
sin un segundo canal de datos paralelo.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# Tamano maximo del event_props serializado a JSON. event_props es un dict
# libre con datos especificos por tipo de evento (href del link, scroll %,
# campo del form). 2 KB acota el volumen y evita payloads abusivos.
EVENT_PROPS_MAX_BYTES = 2048


class TrackEventMeta(BaseModel):
    """Contexto HTTP de la request que el handler extrae del evento.

    El handler la arma desde headers/requestContext del evento API GW:
    `ip` via shared.ip_extractor.extract_ip, `country` via
    extract_country, `user_agent` del header User-Agent. El controller
    la usa para el rate-limit y el enrichment sin tocar el evento crudo.
    """

    ip: str = Field(default='')
    country: str | None = Field(default=None)
    user_agent: str | None = Field(default=None)
    # bypass_secret no se usa en tracking (no hay Turnstile estricto), pero
    # el http_handler generico siempre lo inyecta para uniformidad. Se
    # acepta para no romper el extra:forbid del sub-modelo.
    bypass_secret: str | None = Field(default=None)

    model_config = {'extra': 'forbid'}


class TrackEventModel(BaseModel):
    """Valida el payload de tracking/track (body POST /track + `meta`).

    Reune el body de tracking que envia el cliente y el `meta` con el
    contexto HTTP. `extra` queda en 'forbid' para rechazar campos no
    declarados, igual que el `TrackingEventInput` original.
    """

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

    # Contexto HTTP que el handler inyecta (IP / country / User-Agent).
    # Default vacio: si el handler no lo provee, el modelo no rompe. El
    # http_handler generico lo inyecta como `_meta` (con guion bajo, mismo
    # patron que contact_form para consistencia); aqui se acepta via alias.
    meta: TrackEventMeta = Field(
        default_factory=TrackEventMeta, alias='_meta'
    )

    @field_validator('event_props')
    @classmethod
    def validate_event_props_size(
        cls, v: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Valida que event_props serializado a JSON no exceda el limite.

        event_props es un dict libre; un payload abusivo inflaria el item
        de DynamoDB y la fila de Neon. Se serializa a JSON y se mide en
        bytes. Si excede EVENT_PROPS_MAX_BYTES, lanza ValueError que
        Pydantic convierte en ValidationError.
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
        """Valida que el valor sea un UUID bien formado.

        El cliente puede enviar el UUID con o sin guiones (`event_id` se
        genera con `crypto.randomUUID()` y a veces se compacta). Se acepta
        cualquiera de las dos formas y se devuelve el string original;
        `UUID()` lanza ValueError si el formato es invalido.
        """
        UUID(v)
        return v

    # populate_by_name permite que `meta` se asigne tanto por el alias
    # `_meta` (inyectado por http_handler) como por el nombre del campo
    # (compatibilidad con codigo que ya pasaba `meta` directo).
    model_config = {'extra': 'forbid', 'populate_by_name': True}

    def tracking_payload(self) -> dict[str, Any]:
        """Devuelve el payload de tracking validado, sin `cf_token` ni `meta`.

        Es el dict que el service usa como `validated_input`: los campos
        que el cliente envia, sin el `cf_token` (best-effort, no se
        persiste), sin el `meta` (la IP/country/UA se pasan aparte) y sin
        los valores None (se omiten para no inflar el item).
        """
        return self.model_dump(
            exclude={'cf_token', 'meta'},
            exclude_none=True,
        )
