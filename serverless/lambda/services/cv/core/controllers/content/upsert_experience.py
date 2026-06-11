"""Controller `content.upsert-experience` — Upsert completo de una experiencia: fila + bullets + skills + i18n + niches + priorities.

Admin-only (access JWT + whitelist SSM). Valida el payload con
`ExperienceIn` (shape YAML del seed), delega en
`content_service.upsert_entity` (UNA transaccion + invalidacion del
cache tag 'cv') y normaliza la salida.
"""

from __future__ import annotations

from models.content import ExperienceIn

from .._base import ContentUpsertBase


class UpsertExperience(ContentUpsertBase):
    """Upsert de experience (action `upsert-experience`)."""

    event_model = ExperienceIn
    entity = 'experience'
