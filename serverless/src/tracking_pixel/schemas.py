"""Pydantic schemas para tracking pixel."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TrackingEventInput(BaseModel):
    """Body schema POST /track."""

    # Session: cliente genera UUID4 en localStorage al primer visit
    session_id: str = Field(..., min_length=20, max_length=64)

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
