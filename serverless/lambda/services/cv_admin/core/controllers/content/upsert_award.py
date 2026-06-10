"""Controller `content.upsert-award` — Upsert de un premio + i18n (title/motivation) + niches + priorities.

Admin-only (access JWT + whitelist SSM). Valida el payload con
`AwardIn` (shape YAML del seed), delega en
`content_service.upsert_entity` (UNA transaccion + invalidacion del
cache tag 'cv') y normaliza la salida.
"""

from __future__ import annotations

from models.content_simple import AwardIn

from .._base import ContentUpsertBase


class UpsertAward(ContentUpsertBase):
    """Upsert de award (action `upsert-award`)."""

    event_model = AwardIn
    entity = 'award'
