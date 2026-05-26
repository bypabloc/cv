"""Lambda `contact_worker` — consume SQS `portfolio-contact-form-${stage}`.

Entrypoint del worker. Itera los Records del evento SQS y delega cada
mensaje al controller `worker/process` via `run_controller`. Devuelve
`batchItemFailures` para los items que fallaron (persistencia o email),
de modo que SQS los reintenta hasta `max_receive_count=3` antes de
mandarlos a la DLQ.

El handler es delgado: NO contiene logica de negocio (que vive en
`core/services/persistence.py`). Su unico trabajo es:

  1. parsear el body JSON de cada record SQS,
  2. envolverlo en el contrato sintetico `{operation, action, data}`,
  3. llamar a `run_controller`,
  4. coleccionar los messageIds que fallaron.

Handler de la funcion AWS: `core.handler.lambda_handler`.
"""

from __future__ import annotations

import json
import os
import sys

# El handler vive dentro de core/. Agregamos core/ al sys.path para que
# los imports absolutos (models., services., settings., shared.)
# resuelvan en AWS y en invoke local. shared/ se vendoriza en
# core/shared/ por devtools antes del deploy.
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from typing import Any

from aws_lambda_powertools.metrics import MetricUnit
from settings.operations import OPERATIONS
from shared.lambda_kit import build_event_model, run_controller
from shared.observability.logger import logger
from shared.observability.metrics import metrics
from shared.observability.tracer import tracer

__version__ = '1.0.0'

# Clase EventModel ligada al OPERATIONS del Lambda (la construye el kit).
_EVENT_MODEL = build_event_model(OPERATIONS)


@logger.inject_lambda_context(
    log_event=False,
    correlation_id_path='requestContext.requestId',
)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Procesa un batch SQS (batch_size=1 en este worker).

    Parameters
    ----------
    event : dict
        Evento SQS estandar con `Records` (lista de mensajes).
    _context : Any
        Lambda runtime context (no se usa directamente).

    Returns
    -------
    dict
        `{'batchItemFailures': [{'itemIdentifier': <messageId>}, ...]}`.
        Si la lista esta vacia, SQS borra TODOS los mensajes del batch.
        Si un messageId aparece en la lista, SQS lo retiene para retry.
    """
    failures: list[dict[str, str]] = []
    records = event.get('Records', [])

    for record in records:
        message_id = record['messageId']
        try:
            body = json.loads(record['body'])
            result = run_controller(
                {
                    'operation': 'worker',
                    'action': 'process',
                    'data': body,
                },
                event_model=_EVENT_MODEL,
            )
            if not result.is_valid:
                # Fallo de validacion / negocio reportado por el
                # controller: tambien lo re-encolamos para retry SQS.
                metrics.add_metric(
                    name='ContactProcessFailed',
                    unit=MetricUnit.Count,
                    value=1,
                )
                logger.error(
                    'controller returned is_valid=False',
                    extra={
                        'message_id': message_id,
                        'code': result.code,
                        'stage': result.stage,
                    },
                )
                failures.append({'itemIdentifier': message_id})
                continue

            metrics.add_metric(
                name='ContactProcessed',
                unit=MetricUnit.Count,
                value=1,
            )
        except Exception as exc:
            metrics.add_metric(
                name='ContactProcessFailed',
                unit=MetricUnit.Count,
                value=1,
            )
            logger.exception(
                'failed to process contact message',
                extra={
                    'message_id': message_id,
                    'error': str(exc),
                },
            )
            failures.append({'itemIdentifier': message_id})

    return {'batchItemFailures': failures}


# OPERATIONS se importa para forzar el registro de la operacion
# (descubrimiento por convencion); referenciado para evitar F401.
_ = OPERATIONS
