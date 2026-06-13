"""Controller `content.delete-skill-category` — borra un(a) skill_category por slug.

Admin-only (access JWT + whitelist SSM). El delete limpia hijos +
uniones + traducciones polimorficas + prioridades en UNA transaccion
(`content_service.delete_entity`) e invalida el cache tag 'cv'. Slug
inexistente -> 404 SLUG_NOT_FOUND.
"""

from __future__ import annotations

from models.content_simple import DeleteIn

from .._base import ContentDeleteBase


class DeleteSkillCategory(ContentDeleteBase):
    """Delete de skill_category (action `delete-skill-category`)."""

    event_model = DeleteIn
    entity = 'skill_category'
