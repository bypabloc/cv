"""Lambda `tracking_worker` — consume SQS `portfolio-tracking-events-${stage}`.

Procesa batches de hasta 10 mensajes. CADA mensaje se procesa por
separado pero TODOS comparten la MISMA conexion Neon (cold-start de
Neon amortizado entre los 10 events). Si un mensaje falla, se devuelve
en `batchItemFailures` con su `messageId` original — SQS borra los
exitosos y reintenta SOLO los fallidos (`ReportBatchItemFailures`).

Decision (no usar `run_controller`): el handler invoca directo el
controller `ProcessBatch` con la lista completa de records ya
parseados (`ProcessBatch(validated_data=parsed).execute()`). NO se
usa `run_controller` por mensaje individual porque queremos compartir
la `db_session()` entre los 10 — el ciclo estandar
`preload->validate->execute` esta pensado para 1 evento, 1 controller.
Es una excepcion deliberada al patron documentada arriba y en el
controller.

El Handler de la funcion AWS es `core.handler.lambda_handler`.
"""

from __future__ import annotations

import os
import sys

# El handler vive dentro de core/. Agregamos core/ al sys.path para
# que los imports absolutos (`models.`, `services.`, `settings.`,
# `controllers.`, `shared.`) resuelvan en AWS y en invoke local.
# `shared/` se vendoriza en `core/shared/` por devtools.
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

import json
from typing import Any

from aws_lambda_powertools.metrics import MetricUnit
from controllers.worker.process_batch import ProcessBatch
from settings.operations import OPERATIONS
from shared.lambda_kit import build_event_model
from shared.observability.logger import logger
from shared.observability.metrics import metrics
from shared.observability.tracer import tracer

__version__ = '1.0.0'

# Construimos `_EVENT_MODEL` por uniformidad con el resto del backend
# (no se usa para validar el batch SQS — ese parseo lo hace el handler
# inline y la validacion Pydantic individual ocurre dentro del
# controller via `TrackingQueueMessage`).
_EVENT_MODEL = build_event_model(OPERATIONS)


@logger.inject_lambda_context(
    log_event=False, correlation_id_path='requestContext.requestId'
)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Procesa un batch SQS (hasta 10 records). Retorna batchItemFailures.

    Flujo:
    1. Parsea el `body` JSON de cada record. Si el JSON es invalido,
       el record entero va a `parse_failures` con su `messageId` (no
       se intenta reprocesar — el mensaje es estructuralmente roto).
    2. Invoca `ProcessBatch.execute()` con la lista completa de records
       validos. El controller comparte UNA `db_session()` entre todos.
    3. Une `parse_failures` + `failures` del controller y los devuelve
       como `batchItemFailures`. SQS borra los exitosos y reintenta
       solo los fallidos.
    """
    records = event.get('Records', [])
    parsed: list[dict[str, Any]] = []
    parse_failures: list[dict[str, str]] = []

    for record in records:
        msg_id = record.get('messageId', '')
        try:
            body = json.loads(record['body'])
            parsed.append({'message_id': msg_id, 'body': body})
        except (json.JSONDecodeError, KeyError, TypeError):
            logger.exception(
                'malformed JSON in SQS message',
                extra={'message_id': msg_id},
            )
            metrics.add_metric(
                name='TrackingMalformed',
                unit=MetricUnit.Count,
                value=1,
            )
            parse_failures.append({'itemIdentifier': msg_id})

    # Delega TODA la persistencia al controller (1 conexion Neon
    # compartida entre los records validos del batch).
    controller = ProcessBatch(validated_data=parsed)
    result = controller.execute()
    failures = parse_failures + result['data'].get('failures', [])

    processed = len(records) - len(failures)
    metrics.add_metric(
        name='TrackingProcessed',
        unit=MetricUnit.Count,
        value=processed,
    )
    if failures:
        metrics.add_metric(
            name='TrackingFailed',
            unit=MetricUnit.Count,
            value=len(failures),
        )

    return {'batchItemFailures': failures}


# OPERATIONS / _EVENT_MODEL importados para forzar el registro y para
# uniformidad con el resto del backend; referenciados para evitar F401.
_ = OPERATIONS
_ = _EVENT_MODEL
