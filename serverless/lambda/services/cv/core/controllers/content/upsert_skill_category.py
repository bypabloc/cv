"""Controller `content.upsert-skill-category` — Upsert de una categoria de skills + uniones ordenadas a skills + i18n + niches.

Admin-only (access JWT + whitelist SSM). Valida el payload con
`SkillCategoryIn` (shape YAML del seed), delega en
`content_service.upsert_entity` (UNA transaccion + invalidacion del
cache tag 'cv') y normaliza la salida.
"""

from __future__ import annotations

from models.content import SkillCategoryIn

from .._base import ContentUpsertBase


class UpsertSkillCategory(ContentUpsertBase):
    """Upsert de skill_category (action `upsert-skill-category`)."""

    event_model = SkillCategoryIn
    entity = 'skill_category'
