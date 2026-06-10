"""Controller `content.catalogs` — catalogos para los selects del admin.

Admin-only (access JWT + whitelist SSM). Sin payload de negocio: lee
`tax_niches` (orden de presentacion), `cv_skills` y `tax_tech_tags` via
`catalog_service.catalogs` (read-only, no invalida cache).
"""

from __future__ import annotations

from typing import Any

from models.content_simple import CatalogsIn

from .._base import CvAdminControllerBase


class Catalogs(CvAdminControllerBase):
    """Devuelve niches/skills/techTags (action `catalogs`)."""

    event_model = CatalogsIn
    endpoint = '/cv-admin#content'
    service_module = 'services.catalog_service'
    service_name = 'catalogs'

    def service_kwargs(self, data: Any) -> dict[str, Any]:
        """Sin argumentos: el service lee los 3 catalogos completos."""
        return {}
