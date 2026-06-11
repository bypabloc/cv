"""Controller `content.upsert-project` — Upsert completo de un proyecto: fila + case study + metricas + stack + i18n + niches.

Admin-only (access JWT + whitelist SSM). Valida el payload con
`ProjectIn` (shape YAML del seed), delega en
`content_service.upsert_entity` (UNA transaccion + invalidacion del
cache tag 'cv') y normaliza la salida.
"""

from __future__ import annotations

from models.content import ProjectIn

from .._base import ContentUpsertBase


class UpsertProject(ContentUpsertBase):
    """Upsert de project (action `upsert-project`)."""

    event_model = ProjectIn
    entity = 'project'
