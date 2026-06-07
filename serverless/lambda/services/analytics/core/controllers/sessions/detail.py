"""Controller sessions/detail — detalle de UNA sesion."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.sessions import DetailInput


class Detail(AnalyticsControllerBase):
    """Detalle de una sesion: datos + visitas + count de eventos.

    El _base mapea NotFoundError (subclase de ServiceError, code 4040) a
    `{is_valid: False, code: 4040}` (AC-11).
    """

    event_model = DetailInput
    service_module = 'services.sessions_service'
    service_name = 'detail'

    def service_kwargs(self, data: DetailInput) -> dict[str, Any]:
        return {'session_id': data.session_id}
