"""Pydantic schemas para validar input/output del form de contacto."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from common.validators import sanitize_text


class ContactFormInput(BaseModel):
    """Body schema esperado del POST /contact."""

    # Campos obligatorios
    name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    message: str = Field(..., min_length=10, max_length=5000)

    # Captcha token (Cloudflare Turnstile)
    cf_token: str = Field(..., min_length=20, max_length=2048)

    # Campos opcionales (form progresivo)
    company: str | None = Field(default=None, max_length=200)
    role: str | None = Field(default=None, max_length=100)
    service_type: Literal['consulting', 'fulltime', 'contract', 'other'] | None = None
    budget: str | None = Field(default=None, max_length=100)
    timeline: str | None = Field(default=None, max_length=100)

    # Niche del subdominio (apex/generic | hub | fintech | architect | leader | vibe)
    niche: str | None = Field(default=None, max_length=50)

    @field_validator('name', 'message', 'company', 'role', 'budget', 'timeline')
    @classmethod
    def sanitize_strings(cls, v: str | None) -> str | None:
        """Trim + HTML-escape strings de input para prevenir XSS en email render."""
        if v is None:
            return None
        return sanitize_text(v, max_length=5000)


class ContactCreatedOutput(BaseModel):
    """Respuesta 201 cuando el form se procesa correctamente."""

    contact_id: str
    created_at: str  # ISO 8601 UTC
