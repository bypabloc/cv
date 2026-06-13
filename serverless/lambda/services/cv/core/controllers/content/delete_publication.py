"""Controller `content.delete-publication` — borra un(a) publication por slug.

Admin-only (access JWT + whitelist SSM). El delete limpia hijos +
uniones + traducciones polimorficas + prioridades en UNA transaccion
(`content_service.delete_entity`) e invalida el cache tag 'cv'. Slug
inexistente -> 404 SLUG_NOT_FOUND.
"""

from __future__ import annotations

from models.content_simple import DeleteIn

from .._base import ContentDeleteBase


class DeletePublication(ContentDeleteBase):
    """Delete de publication (action `delete-publication`)."""

    event_model = DeleteIn
    entity = 'publication'
