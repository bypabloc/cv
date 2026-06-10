"""Controller `content.upsert-profile` — Upsert del profile singleton (handle como clave natural) + stats + i18n + niches.

Admin-only (access JWT + whitelist SSM). Valida el payload con
`ProfileIn` (shape YAML del seed), delega en
`content_service.upsert_entity` (UNA transaccion + invalidacion del
cache tag 'cv') y normaliza la salida.
"""

from __future__ import annotations

from models.content import ProfileIn

from .._base import ContentUpsertBase


class UpsertProfile(ContentUpsertBase):
    """Upsert de profile (action `upsert-profile`)."""

    event_model = ProfileIn
    entity = 'profile'
