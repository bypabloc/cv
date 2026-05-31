"""Lambda `send_email` — envio de email transaccional (invoke async).

Entrypoint del Lambda. Router delgado: recibe el evento del invoke async
`{operation:'email', action:'send', data:{kind, to, data, reply_to}}`,
resuelve el controller y ejecuta su ciclo. NO expone HTTP (trigger direct):
lo invocan contact_form / auth / users con `InvocationType='Event'`.

La logica (config DynamoDB + template S3 + render Jinja2 + SES) vive en
`services/email_service.py`. NO toca Neon (Lambda puro).

El Handler de la funcion AWS es `core.handler.lambda_handler`.
"""

from __future__ import annotations

import os
import sys

# El handler vive dentro de core/. Agregamos core/ al sys.path para que
# los imports absolutos (models., services., settings., shared.) resuelvan
# en AWS y en invoke local. shared/ se vendoriza en core/shared/.
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from typing import Any

from models.event import EVENT_MODEL
from settings.operations import OPERATIONS
from shared.lambda_kit.dispatch import run_controller
from shared.observability.logger import logger
from shared.observability.metrics import MetricUnit, metrics

__version__ = '1.0.0'


@logger.inject_lambda_context(log_event=False)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Procesa el evento de envio de email (invoke async, fire-and-forget).

    El caller no espera el resultado (InvocationType='Event'). Devuelve un
    dict de status para CloudWatch / logs. Un error de negocio (kind
    desconocido, render, SES) se loggea + metrica; NO se re-lanza (no hay a
    quien devolverlo en async).
    """
    operation = event.get('operation')
    action = event.get('action')
    if operation != 'email' or not action:
        logger.warning('evento send_email invalido', extra={'event': event})
        metrics.add_metric(name='EmailError', unit=MetricUnit.Count, value=1)
        return {'status': 'error', 'error': 'evento invalido'}

    try:
        result = run_controller(event, EVENT_MODEL)
    except Exception:
        logger.exception('send_email fallo')
        metrics.add_metric(name='EmailError', unit=MetricUnit.Count, value=1)
        return {'status': 'error', 'error': 'fallo interno — ver CloudWatch'}

    if not result.is_valid:
        logger.warning('send_email rechazado', extra={'data': result.data})
        metrics.add_metric(name='EmailRejected', unit=MetricUnit.Count, value=1)
        return {'status': 'rejected', 'data': result.data, 'code': result.code}

    metrics.add_metric(name='EmailSent', unit=MetricUnit.Count, value=1)
    return {'status': 'ok', 'data': result.data}


# OPERATIONS se importa para forzar el registro de la operacion `email`
# (descubrimiento por convencion); referenciado para evitar F401.
_ = OPERATIONS
