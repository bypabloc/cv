"""Lambda `tracking_writer` — persiste 1 evento de tracking en Neon.

Entrypoint del Lambda. Invocado de forma ASINCRONA por el encoder
`tracking_pixel` (`InvocationType='Event'`, sin SQS): el encoder valida +
pre-genera los IDs fisicos (`page_id` UUIDv7, `created_at`) y delega la
escritura a Neon a este Lambda, fuera del request del cliente.

El evento que recibe YA viene en el contrato estandar lambda-controller:

    {
      "operation": "tracking",
      "action": "write",
      "data": { "schema_version": 1, "page_id": "...", "session_id": "...",
                "event_id": "...", ... }
    }

El handler es un router delgado: pasa el evento a `run_controller`, que
valida + resuelve el controller `tracking/write` + ejecuta su ciclo. La
logica de persistencia vive en `services/persistence.py`.

NO procesa batches: cada invoke async trae UN evento. AWS reintenta el
invoke async automaticamente (2 reintentos) si el handler lanza; por eso
ante un fallo de persistencia se RE-LANZA (no se traga) para que AWS
reintente y, agotados los reintentos, mande el evento a la DLQ de la
funcion si esta configurada.

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

from typing import Any

import shared.db.models.visitor.session
import shared.db.models.visitor.session_visit
import shared.db.models.visitor.tracking  # noqa: F401
from settings.operations import OPERATIONS
from shared.db.warmup import warm_db
from shared.lambda_kit.dispatch import run_controller
from shared.lambda_kit.event_model import build_event_model
from shared.observability.logger import logger
from shared.observability.metrics import MetricUnit, metrics

__version__ = '2.0.0'

# Clase EventModel ligada al OPERATIONS del Lambda (la construye el kit).
_EVENT_MODEL = build_event_model(OPERATIONS)

# SnapStart: precalienta engine (NullPool) + configure_mappers del dominio
# visitor en el INIT -> queda en el snapshot. Best-effort.
warm_db()


@logger.inject_lambda_context(log_event=False)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Persiste 1 evento de tracking en Neon (invoke async del encoder).

    El `event` ya viene en `{operation, action, data}` (lo arma el encoder
    `tracking_pixel` en `invoke_tracking_writer`). Se delega a
    `run_controller`; un fallo de validacion/persistencia se RE-LANZA para
    que AWS reintente el invoke async.
    """
    result = run_controller(event, _EVENT_MODEL)

    if result.stage == 'validation' or not result.is_valid:
        logger.error(
            'tracking_writer: evento invalido o fallo de persistencia',
            extra={'stage': result.stage, 'code': result.code},
        )
        metrics.add_metric(
            name='TrackingWriteFailed', unit=MetricUnit.Count, value=1
        )
        # RE-LANZA: AWS reintenta el invoke async (2 reintentos) y, agotados,
        # manda el evento a la DLQ de la funcion (si esta configurada).
        msg = f'tracking write failed (stage={result.stage})'
        raise RuntimeError(msg)

    metrics.add_metric(name='TrackingWritten', unit=MetricUnit.Count, value=1)
    return result.data


# OPERATIONS importado para forzar el registro de la operation `tracking`
# (descubrimiento por convencion); referenciado para evitar F401.
_ = OPERATIONS
