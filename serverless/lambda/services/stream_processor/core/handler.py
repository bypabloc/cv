"""Lambda `stream_processor` — DynamoDB Streams -> replica Neon PostgreSQL.

Entrypoint del Lambda. Router delgado: traduce el evento real de
DynamoDB Streams (`{Records: [...]}`) al contrato del estandar
lambda-controller `{operation, action, data}`, resuelve el controller y
devuelve el resultado. La logica de negocio vive en
`services/stream_service.py`.

Triggered por el Event Source Mapping de los DynamoDB Streams (contacts
+ tracking). Devuelve `batchItemFailures` para que AWS reintente solo
los records fallidos (los demas avanzan).

El Handler de la funcion AWS es `core.handler.lambda_handler`.

`DATABASE_URL` la inyecta devtools desde SSM; el ORM
(`shared.db.session`) la resuelve via `shared.db.url`. El nucleo
`validate_event -> controller -> run` lo provee
`shared.lambda_kit.run_controller`.
"""

from __future__ import annotations

import os
import sys

# El handler vive dentro de core/. Agregamos core/ al sys.path para que
# los imports absolutos (models., services., settings., shared.)
# resuelvan en AWS y en invoke local. shared/ se vendoriza en core/shared/.
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from typing import Any

from settings.operations import OPERATIONS
from shared.lambda_kit import build_event_model, run_controller
from shared.observability import MetricUnit, logger, metrics, tracer

__version__ = '3.0.0'

# Clase EventModel ligada al OPERATIONS del Lambda (la construye el kit).
_EVENT_MODEL = build_event_model(OPERATIONS)


def _all_failed(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Reporta TODOS los records del batch como fallidos.

    Se usa cuando no se puede procesar el batch (evento invalido o fallo
    inesperado del controller): AWS reintenta todo, no se pierde nada.
    """
    failed_ids = [
        r.get('eventID', '') for r in records if r.get('eventID')
    ]
    metrics.add_metric(
        name='StreamRecordsFailed',
        unit=MetricUnit.Count,
        value=len(failed_ids),
    )
    return {
        'batchItemFailures': [
            {'itemIdentifier': eid} for eid in failed_ids
        ],
    }


@logger.inject_lambda_context(log_event=False)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Procesa una batch de records del DynamoDB Stream.

    Traduce `{Records: [...]}` al evento sintetico
    `{operation: 'stream', action: 'process', data: {records: [...]}}`,
    valida, enruta al controller `Process` y devuelve EXACTAMENTE
    `{'batchItemFailures': [{'itemIdentifier': eid}, ...]}` — el
    contrato `ReportBatchItemFailures` de AWS.
    """
    records = event.get('Records', [])

    # Sintesis del evento estandar {operation, action, data}.
    synthetic_event = {
        'operation': 'stream',
        'action': 'process',
        'data': {'records': records},
    }

    # --- Validar evento + resolver controller + ejecutar (kit) ---
    try:
        result = run_controller(synthetic_event, _EVENT_MODEL)
    except Exception:
        logger.exception('stream batch processing failed')
        # Fallo inesperado del controller: reintentamos todo el batch.
        return _all_failed(records)

    if result.stage == 'validation':
        logger.error(
            'stream event validation failed',
            extra={'validation_error': result.data},
        )
        # Sin un controller resuelto no podemos procesar el batch.
        return _all_failed(records)

    if not result.is_valid:
        # El controller `Process` NUNCA devuelve is_valid: False por un
        # record fallido (los reporta en failed_record_ids). Un is_valid
        # False aqui es defensivo: reintentamos todo el batch.
        logger.error('stream controller reported failure')
        return _all_failed(records)

    processed = result.data.get('processed', 0)
    skipped = result.data.get('skipped', 0)
    failed_record_ids = result.data.get('failed_record_ids', [])

    metrics.add_metric(
        name='StreamRecordsProcessed',
        unit=MetricUnit.Count,
        value=processed,
    )
    metrics.add_metric(
        name='StreamRecordsSkipped',
        unit=MetricUnit.Count,
        value=skipped,
    )
    if failed_record_ids:
        metrics.add_metric(
            name='StreamRecordsFailed',
            unit=MetricUnit.Count,
            value=len(failed_record_ids),
        )

    # `ReportBatchItemFailures`: los records de `batchItemFailures` se
    # reintenta; los OK avanzan.
    return {
        'batchItemFailures': [
            {'itemIdentifier': eid} for eid in failed_record_ids
        ],
    }
