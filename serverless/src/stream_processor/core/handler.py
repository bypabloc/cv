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

`DATABASE_URL` la inyecta el template SAM desde SSM; el ORM
(`shared.db.session`) la resuelve via `shared.db.url`.
"""

from __future__ import annotations

import os
import sys

# El handler vive dentro de core/. Agregamos core/ al sys.path para que
# los imports absolutos (models., services., settings., utils., shared.)
# resuelvan en AWS y en invoke local. shared/ se vendoriza en core/shared/.
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from typing import Any

from aws_lambda_powertools.metrics import MetricUnit
from settings.operations import OPERATIONS
from utils.validation.event import validate_event

from shared.observability.logger import logger
from shared.observability.metrics import metrics
from shared.observability.tracer import tracer

__version__ = '2.0.0'


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

    # --- Validar evento + resolver controller (operation + action) ---
    validation_result = validate_event(synthetic_event)
    if not validation_result.get('is_valid'):
        logger.error(
            'stream event validation failed',
            extra={'message': validation_result.get('message')},
        )
        # Sin un controller resuelto no podemos procesar el batch.
        # Reportamos TODOS los records como fallidos para que AWS los
        # reintente (no se pierde nada).
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

    validated_event = validation_result['data']
    controller_data = validated_event.controller_info.get('data', {})
    controller_class = controller_data.get('controller_class')

    # --- Ejecutar el controller (preload -> validate -> execute) ---
    try:
        instance = controller_class(
            event=validated_event.controller_event,
        )
        result = instance.run()
    except Exception:
        logger.exception('stream batch processing failed')
        # Fallo inesperado del controller: reintentamos todo el batch.
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

    result_data = result.get('data', {})
    processed = result_data.get('processed', 0)
    skipped = result_data.get('skipped', 0)
    failed_record_ids = result_data.get('failed_record_ids', [])

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


# OPERATIONS se importa para forzar el registro de la operacion `stream`
# (descubrimiento por convencion); referenciado para evitar F401.
_ = OPERATIONS
