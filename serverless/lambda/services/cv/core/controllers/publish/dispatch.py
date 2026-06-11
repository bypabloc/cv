"""Controller `publish.dispatch` — dispara el deploy de las apps.

Admin-only (access JWT + whitelist SSM). Sin payload de negocio: el ref
lo resuelve el service desde el stage del Lambda (dev -> `dev`, prod ->
`main`). Delega en `publish_service.dispatch` (workflow_dispatch de
deploy-apps.yml via la GitHub API). Rate-limit propio MAS estricto
(`/cv#publish.dispatch`, ~3/min): cada dispatch es un trigger de CI.
"""

from __future__ import annotations

from typing import Any

from models.publish import PublishDispatchIn

from .._base import CvAdminControllerBase


class Dispatch(CvAdminControllerBase):
    """Dispara el workflow de deploy (action `dispatch`)."""

    event_model = PublishDispatchIn
    endpoint = '/cv#publish.dispatch'
    service_module = 'services.publish_service'
    service_name = 'dispatch'

    def service_kwargs(self, data: Any) -> dict[str, Any]:
        """Sin argumentos: el service resuelve ref + token por stage."""
        return {}
