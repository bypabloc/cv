"""Lambda `db` — gestion del schema PostgreSQL del portfolio.

Entrypoint del Lambda. Router delgado: traduce el payload de invocacion
`{command, args}` al contrato del estandar lambda-controller
`{operation, action, data}`, resuelve el controller y devuelve el
resultado. La logica de negocio vive en `services/db_service.py`, que a
su vez delega en `shared.db`.

Invocacion (no via API Gateway — invoke directo / deploy hook):

    {"command": "migrate"}
    {"command": "show-migrations"}
    {"command": "current"}
    {"command": "stamp", "args": {"target": "head"}}
    {"command": "downgrade", "args": {"target": "-1", "confirm": true}}

El Handler de la funcion AWS es `core.handler.lambda_handler`.

`DATABASE_URL` la inyecta devtools desde SSM; Alembic la lee en su
`env.py`. `ensure_database_url` la resuelve antes de ejecutar el
controller. El nucleo `validate_event -> controller -> run` lo provee
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
from shared.db.url import ensure_database_url
from shared.lambda_kit import build_event_model, run_controller
from shared.observability import MetricUnit, logger, metrics
from shared.observability.tracer import tracer

__version__ = '3.0.0'

# Clase EventModel ligada al OPERATIONS del Lambda (la construye el kit).
_EVENT_MODEL = build_event_model(OPERATIONS)

# El command de invocacion `show-migrations` (con guion) mapea a la
# action `show_migrations` (con underscore) para que el modulo y la clase
# del controller sean identificadores Python validos.
_COMMAND_TO_ACTION = {
    'show-migrations': 'show_migrations',
}


def _list_actions() -> list[str]:
    """Descubre las actions de la operation `db` desde controllers/db/."""
    controllers_dir = os.path.join(_CORE_DIR, 'controllers', 'db')
    actions: list[str] = []
    for entry in os.listdir(controllers_dir):
        if entry.endswith('.py') and not entry.startswith('_'):
            actions.append(entry[:-3])
    return actions


def _available_commands() -> list[str]:
    """Lista de commands soportados (los inversos del mapeo de actions)."""
    actions = _list_actions()
    inverse = {v: k for k, v in _COMMAND_TO_ACTION.items()}
    return sorted(inverse.get(a, a) for a in actions)


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Traduce {command, args} a {operation, action, data} y enruta."""
    command_name = event.get('command')

    if not command_name:
        logger.warning('invocacion sin command')
        return {
            'status': 'error',
            'error': "Falta 'command' en el payload.",
            'available': _available_commands(),
        }

    args = event.get('args', {})
    if not isinstance(args, dict):
        return {
            'status': 'error',
            'error': "'args' debe ser un objeto.",
        }

    action = _COMMAND_TO_ACTION.get(command_name, command_name)

    # Sintesis del evento estandar {operation, action, data}.
    synthetic_event = {
        'operation': 'db',
        'action': action,
        'data': args,
    }

    logger.info('ejecutando command', extra={'command': command_name})

    # --- Resolver DATABASE_URL antes de ejecutar el controller ---
    try:
        ensure_database_url()
    except Exception:
        logger.exception('no se pudo resolver DATABASE_URL')
        metrics.add_metric(
            name='DbCommandFailed', unit=MetricUnit.Count, value=1
        )
        return {
            'status': 'error',
            'command': command_name,
            'error': 'No se pudo resolver DATABASE_URL — ver CloudWatch.',
        }

    # --- Validar evento + resolver controller + ejecutar (kit) ---
    try:
        result = run_controller(synthetic_event, _EVENT_MODEL)
    except Exception:
        logger.exception('command fallo', extra={'command': command_name})
        metrics.add_metric(
            name='DbCommandFailed', unit=MetricUnit.Count, value=1
        )
        return {
            'status': 'error',
            'command': command_name,
            'error': 'El command fallo — ver los logs de CloudWatch.',
        }

    if result.stage == 'validation':
        logger.warning(
            'command desconocido',
            extra={'command': command_name},
        )
        metrics.add_metric(
            name='DbCommandFailed', unit=MetricUnit.Count, value=1
        )
        return {
            'status': 'error',
            'error': f"command desconocido: '{command_name}'.",
            'available': _available_commands(),
        }

    if not result.is_valid:
        metrics.add_metric(
            name='DbCommandFailed', unit=MetricUnit.Count, value=1
        )
        return {
            'status': result.data.get('status', 'error'),
            'command': command_name,
            'error': result.data.get('message', 'El command fallo.'),
        }

    metrics.add_metric(name='DbCommandOk', unit=MetricUnit.Count, value=1)
    return result.data
