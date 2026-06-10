"""Controller `publish.status` — estado del ultimo deploy de las apps.

Admin-only (access JWT + whitelist SSM). Sin payload de negocio: delega
en `publish_service.status`, que consulta el run mas reciente de
deploy-apps.yml para el ref del stage (o `{status: 'none'}` si no hay).
"""

from __future__ import annotations

from typing import Any

from models.publish import PublishStatusIn

from .._base import CvAdminControllerBase


class Status(CvAdminControllerBase):
    """Consulta el ultimo run del workflow (action `status`)."""

    event_model = PublishStatusIn
    endpoint = '/cv-admin#publish.status'
    service_module = 'services.publish_service'
    service_name = 'status'

    def service_kwargs(self, data: Any) -> dict[str, Any]:
        """Sin argumentos: el service resuelve ref + token por stage."""
        return {}
