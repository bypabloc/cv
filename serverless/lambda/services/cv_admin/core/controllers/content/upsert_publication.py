"""Controller `content.upsert-publication` — Upsert de una publicacion + i18n (summary) + niches + priorities.

Admin-only (access JWT + whitelist SSM). Valida el payload con
`PublicationIn` (shape YAML del seed), delega en
`content_service.upsert_entity` (UNA transaccion + invalidacion del
cache tag 'cv') y normaliza la salida.
"""

from __future__ import annotations

from models.content_simple import PublicationIn

from .._base import ContentUpsertBase


class UpsertPublication(ContentUpsertBase):
    """Upsert de publication (action `upsert-publication`)."""

    event_model = PublicationIn
    entity = 'publication'
