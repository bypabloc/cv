"""Controller `content.upsert-endorsement` — Upsert de una recomendacion + i18n (relation) + niches + priorities.

Admin-only (access JWT + whitelist SSM). Valida el payload con
`EndorsementIn` (shape YAML del seed), delega en
`content_service.upsert_entity` (UNA transaccion + invalidacion del
cache tag 'cv') y normaliza la salida.
"""

from __future__ import annotations

from models.content_simple import EndorsementIn

from .._base import ContentUpsertBase


class UpsertEndorsement(ContentUpsertBase):
    """Upsert de endorsement (action `upsert-endorsement`)."""

    event_model = EndorsementIn
    entity = 'endorsement'
