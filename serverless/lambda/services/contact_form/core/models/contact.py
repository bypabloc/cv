"""Modelos Pydantic de la operacion `contact`.

Un modelo por action. `ContactCreateModel` valida el campo `data` del
evento sintetico que el handler arma a partir del evento HTTP de API
Gateway: los campos del form del visitante MAS un bloque `_meta` con la
metadata de transporte (IP, country, user-agent, bypass-secret) que el
controller necesita para el rate-limit y la validacion Turnstile.

El campo `cf_token` (token de Cloudflare Turnstile) ya venia en el body
del form, asi que vive en el modelo del form, no en `_meta`.

`ContactCreatedOutput` es el contrato de la respuesta 201.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator
from shared.http.validators import sanitize_text


class RequestMeta(BaseModel):
    """Metadata de transporte de la request HTTP.

    El handler la extrae de los headers de API Gateway y la pasa al
    controller dentro de `data._meta`. El service NO la conoce: solo el
    controller la usa para el rate-limit y la verificacion Turnstile.
    """

    ip: str = ''
    country: str | None = None
    user_agent: str | None = None
    bypass_secret: str | None = None
    # Mapa raw de los headers cloudfront-* del request (Edge-Optimized
    # API GW los expone). El service lo persiste en la columna
    # cloudfront_meta JSONB.
    cloudfront_meta: dict[str, str] = Field(default_factory=dict)
    # Origin header raw del request (https://hub.portfolio.dev...). El
    # controller lo usa para inferir niche cuando el form no lo envia
    # (spec sessions-normalize, decision 6).
    origin: str | None = None

    model_config = {'extra': 'forbid'}


class ContactCreateModel(BaseModel):
    """Valida el payload de contact/create.

    Reune los campos del form del visitante (obligatorios + opcionales),
    el `cf_token` de Turnstile y el bloque `_meta` de transporte. Replica
    las reglas del antiguo `ContactFormInput` (longitudes, sanitizacion
    XSS, formato de `session_id`) para que la validacion observable no
    cambie respecto del Lambda plano.
    """

    # Campos obligatorios del form
    name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    message: str = Field(..., min_length=10, max_length=5000)

    # Captcha token (Cloudflare Turnstile).
    # Opcional intencionalmente: si viene vacio, el controller evalua el
    # header X-Turnstile-Bypass-Secret (solo valido en stage in {dev,local}).
    cf_token: str = Field(default='', max_length=2048)

    # Campos opcionales (form progresivo)
    company: str | None = Field(default=None, max_length=200)
    role: str | None = Field(default=None, max_length=100)
    service_type: (
        Literal['consulting', 'fulltime', 'contract', 'other'] | None
    ) = None
    budget: str | None = Field(default=None, max_length=100)
    timeline: str | None = Field(default=None, max_length=100)

    # Niche del subdominio (apex/generic | hub | fintech | architect |
    # leader | vibe).
    niche: str | None = Field(default=None, max_length=50)

    # Session de tracking (cf_session del TrackingPixel). Opcional: un
    # visitante que rechazo el tracking no tiene cf_session -> el contacto
    # se guarda igual sin correlacion. Validado 20-64 chars cuando viene.
    session_id: str | None = Field(default=None, min_length=20, max_length=64)

    # Metadata de transporte que el handler inyecta desde los headers HTTP.
    # No es parte del form: el controller la usa, el service la ignora.
    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = {'extra': 'forbid', 'populate_by_name': True}

    @field_validator('name', 'message', 'company', 'role', 'budget', 'timeline')
    @classmethod
    def sanitize_strings(cls, v: str | None) -> str | None:
        """Trim + HTML-escape de strings de input (previene XSS en email)."""
        if v is None:
            return None
        return sanitize_text(v, max_length=5000)

    def form_fields(self) -> dict:
        """Devuelve los campos del form (sin `cf_token` ni `_meta`).

        Es el payload que el service persiste y usa para el email: el
        equivalente de `parsed.model_dump(exclude={'cf_token'})` del
        Lambda plano. Spec drop-cloudfront-meta: el dict NO incluye
        `cloudfront_meta` (columna dropeada en alembic c3d4e5f6a7b8);
        `RequestMeta.cloudfront_meta` sigue aceptandolo en entrada pero
        ya no se propaga al payload de persistencia.
        """
        return self.model_dump(
            exclude={'cf_token', 'meta'},
            exclude_none=True,
        )


class ContactCreatedOutput(BaseModel):
    """Respuesta 201 cuando el form se procesa correctamente."""

    contact_id: str
    created_at: str  # ISO 8601 UTC
