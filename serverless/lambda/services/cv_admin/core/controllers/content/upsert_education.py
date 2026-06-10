"""Controller `content.upsert-education` — Upsert de una entrada de educacion + i18n + niches + priorities.

Admin-only (access JWT + whitelist SSM). Valida el payload con
`EducationIn` (shape YAML del seed), delega en
`content_service.upsert_entity` (UNA transaccion + invalidacion del
cache tag 'cv') y normaliza la salida.
"""

from __future__ import annotations

from models.content_simple import EducationIn

from .._base import ContentUpsertBase


class UpsertEducation(ContentUpsertBase):
    """Upsert de education (action `upsert-education`)."""

    event_model = EducationIn
    entity = 'education'
