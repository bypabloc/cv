"""Controller worker/process_batch — procesa hasta 10 mensajes en 1 Neon session.

Recibe `validated_data: list[{message_id, body}]`. Itera cada mensaje,
hace `ensure_session_and_visit` + `insert_tracking_idempotent` con
`ON CONFLICT (created_at, visit_id, page_id) DO NOTHING`. Si UNO
falla, se agrega a `failures` y el batch continua con el resto. Toda
la transaccion comparte la misma `db_session`.

Decision deliberada: este controller NO sigue el flujo
`preload->validate->execute` del estandar lambda-controller porque el
"payload" del controller es la lista completa de records del batch
SQS (no un evento individual). El handler lo invoca DIRECTO con
`ProcessBatch(validated_data=parsed)` + `.execute()`. Se documenta
aqui y en el handler para que cualquiera que lea el codigo entienda
la excepcion al patron.

Decision de aislamiento de fallos: cada mensaje del batch se procesa
dentro de `session.begin_nested()` (savepoint Postgres) en el
service `process_tracking_message`. Si UN mensaje rompe (FK
violation, IntegrityError no esperado, etc.) SOLO se revierte SU
savepoint — la transaccion exterior sigue viva y los otros 9 commits
se preservan. Sin savepoint, un fallo aborta la tx entera y
SQLAlchemy lanza InFailedTransactionError en los INSERTS siguientes.
"""

from __future__ import annotations

from typing import Any

from models.message import TrackingQueueMessage
from services.persistence import process_tracking_message
from shared.db.session import db_session
from shared.lambda_kit import BaseController
from shared.observability.logger import logger


class ProcessBatch(BaseController):
    """action = 'process_batch'. Procesa el batch entero con 1 session.

    El nombre de la clase es action.capitalize() (`process_batch` ->
    `Process_batch` no es valido en Python — usamos `ProcessBatch`
    siguiendo PascalCase).
    """

    # event_model: None porque el handler ya valido los records uno por
    # uno via Pydantic dentro de `execute()`. No usamos `validate()` del
    # ciclo estandar.
    event_model = None

    def __init__(
        self,
        *,
        validated_data: list[dict[str, Any]] | None = None,
    ) -> None:
        """Acepta `validated_data` por keyword en vez del `event` del ciclo.

        El handler invoca `ProcessBatch(validated_data=parsed)` con la
        lista completa de records del batch SQS. NO se usa el `event`
        del `BaseController` estandar (el "evento" del worker es el
        batch entero, no un mapeo `{operation, action, data}`).
        """
        # Mantenemos el contrato del BaseController.__init__: pasamos
        # un dict vacio como event para no romper el atributo.
        super().__init__(event={})
        self.validated_data = validated_data or []

    def execute(self) -> dict[str, Any]:
        """Persiste el batch completo en una sola db_session.

        Cada mensaje va en un savepoint dentro del service. Un fallo
        individual NO aborta el resto del batch — se reporta en
        `failures` para que el handler los devuelva en
        `batchItemFailures`.
        """
        records: list[dict[str, Any]] = self.validated_data
        failures: list[dict[str, str]] = []

        # 1 sola conexion Neon para todos los mensajes del batch
        # (cold-start amortizado entre los hasta 10 events).
        with db_session() as session:
            for record in records:
                msg_id = record['message_id']
                try:
                    msg = TrackingQueueMessage(**record['body'])
                    process_tracking_message(session, msg)
                except Exception:
                    logger.exception(
                        'failed to process tracking message',
                        extra={'message_id': msg_id},
                    )
                    failures.append({'itemIdentifier': msg_id})
                    # NO re-raise: continuamos con el resto del batch.
                    # El savepoint del service ya revirtio el INSERT
                    # fallido; la tx exterior sigue viva.

        return {
            'is_valid': True,
            'data': {
                'failures': failures,
                'processed': len(records) - len(failures),
            },
            'code': 0,
        }
