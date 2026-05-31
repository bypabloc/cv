"""Controller tracking/write — persiste 1 tracking_event en Neon.

Recibe el `data` del invoke async (el mensaje que arma el encoder
`tracking_pixel` en `invoke_tracking_writer`), validado por el
`event_model` `TrackingWriteModel`. Abre UNA `db_session()` y delega la
escritura a `services.persistence.process_tracking_message`
(`ensure_session_and_visit` + `insert_tracking_idempotent` con
`ON CONFLICT (created_at, visit_id, page_id) DO NOTHING`).

Sigue el ciclo estandar lambda-controller (`preload -> validate ->
execute`): el invoke async trae UN evento, asi que NO hay batch ni
`db_session` compartida (a diferencia del worker SQS que reemplaza).

Un fallo de persistencia se PROPAGA (no se traga): el handler lo
convierte en un RuntimeError para que AWS reintente el invoke async.
"""

from __future__ import annotations

from typing import Any

from models.message import TrackingWriteModel
from services.persistence import process_tracking_message
from shared.db.session import db_session
from shared.lambda_kit.base_controller import BaseController
from shared.observability.logger import logger


class Write(BaseController):
    """action = 'write'. Persiste 1 tracking_event en Neon.

    El nombre de la clase es action.capitalize() ('write' -> 'Write').
    """

    event_model = TrackingWriteModel

    def execute(self) -> dict[str, Any]:
        """Persiste el evento en Neon (1 tx). Propaga el fallo al handler."""
        msg: TrackingWriteModel = self.validated_data  # type: ignore[assignment]

        with db_session() as session:
            inserted = process_tracking_message(session, msg)

        logger.info(
            'tracking event written',
            extra={
                'page_id': msg.page_id,
                'session_id': msg.session_id,
                'inserted': inserted,
            },
        )
        return {
            'is_valid': True,
            'data': {
                'operation': 'tracking',
                'action': 'write',
                'page_id': msg.page_id,
                'session_id': msg.session_id,
                'inserted': inserted,
            },
            'code': 0,
        }
