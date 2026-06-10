"""Controller `content.reorder` — reescribe prioridades por niche.

Admin-only (access JWT + whitelist SSM). Valida `{entity_type, niche,
ordered_slugs}` con `ReorderIn` y delega en `reorder_service.reorder`:
exige que `ordered_slugs` sea EXACTAMENTE el conjunto de entidades del
niche (mismatch -> 400 REORDER_SLUGS_MISMATCH con faltantes/sobrantes) y
reescribe `tax_niche_priorities` en orden descendente.
"""

from __future__ import annotations

from typing import Any

from models.content_simple import ReorderIn

from .._base import CvAdminControllerBase


class Reorder(CvAdminControllerBase):
    """Reordena las prioridades de un niche (action `reorder`)."""

    event_model = ReorderIn
    endpoint = '/cv-admin#content'
    service_module = 'services.reorder_service'
    service_name = 'reorder'

    def service_kwargs(self, data: Any) -> dict[str, Any]:
        """Pasa entity_type + niche + ordered_slugs al service."""
        return {
            'entity_type': data.entity_type,
            'niche': data.niche,
            'ordered_slugs': list(data.ordered_slugs),
        }
