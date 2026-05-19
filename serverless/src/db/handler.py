"""Lambda `db` — gestion del schema PostgreSQL del portfolio.

Una sola Lambda con estructura factory: el payload de invocacion trae un
`command`; el handler lo resuelve contra el registry `COMMANDS` y lo
ejecuta. Escala agregando modulos en `commands/` (no se toca el handler).

Invocacion (no via API Gateway — invoke directo / deploy hook):

    {"command": "migrate"}
    {"command": "show-migrations"}
    {"command": "current"}
    {"command": "stamp", "args": {"target": "head"}}
    {"command": "downgrade", "args": {"target": "-1", "confirm": true}}

`DATABASE_URL` la inyecta el template SAM desde SSM; Alembic la lee en su
`env.py`.
"""

from typing import Any

from aws_lambda_powertools.metrics import MetricUnit

from _shared.db.url import ensure_database_url
from _shared.logger import logger
from _shared.metrics import metrics
from _shared.tracer import tracer
from db.commands import COMMANDS


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Resuelve el `command` del payload y lo ejecuta via el registry."""
    command_name = event.get('command')

    if not command_name:
        logger.warning('invocacion sin command')
        return {
            'status': 'error',
            'error': "Falta 'command' en el payload.",
            'available': sorted(COMMANDS),
        }

    handler = COMMANDS.get(command_name)
    if handler is None:
        logger.warning('command desconocido', extra={'command': command_name})
        return {
            'status': 'error',
            'error': f"command desconocido: '{command_name}'.",
            'available': sorted(COMMANDS),
        }

    args = event.get('args', {})
    if not isinstance(args, dict):
        return {
            'status': 'error',
            'error': "'args' debe ser un objeto.",
        }

    logger.info('ejecutando command', extra={'command': command_name})
    try:
        # Resuelve DATABASE_URL desde SSM (o respeta la del entorno) antes
        # de que cualquier comando construya el Config de Alembic.
        ensure_database_url()
        result = handler(args)
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

    metrics.add_metric(
        name='DbCommandOk', unit=MetricUnit.Count, value=1
    )
    return result
