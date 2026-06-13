"""Controller `content.get-all` — CV completo en shape de edicion.

Admin-only (access JWT + whitelist SSM via `required_permission`).
Devuelve las 10 secciones del CV (incluida `publications`, sin lectura
publica) SIN filtrar por niche, resueltas en UNA sola sesion Neon
(`cv_service.get_all_admin`). Es la lectura unica del editor del admin:
el overview pasa de ~10 requests a 1.
"""

from __future__ import annotations

from typing import Any

from models.content_simple import GetAllIn

from .._base import CvAdminControllerBase


class GetAll(CvAdminControllerBase):
    """Devuelve el CV completo de edicion (action `get-all`)."""

    event_model = GetAllIn
    endpoint = '/cv#content'
    service_module = 'services.cv_service'
    service_name = 'get_all_admin'

    def service_kwargs(self, data: Any) -> dict[str, Any]:
        """Sin argumentos: el service trae las 10 secciones completas."""
        return {}
