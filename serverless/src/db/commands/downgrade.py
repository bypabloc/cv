"""@command downgrade — revierte migraciones (`alembic downgrade`).

OPERACION DESTRUCTIVA: requiere confirmacion explicita en el payload.

Payload: `{"command": "downgrade", "args": {"target": "-1", "confirm": true}}`
- `target`  : revision destino (`-1`, `base`, o una revision). Obligatorio.
- `confirm` : debe ser `true`. Sin el, el comando NO ejecuta nada — es la
              salvaguarda contra un downgrade accidental en prod.
"""

from typing import Any

from alembic import command

from db.alembic_runner import build_config


def run(args: dict[str, Any]) -> dict[str, Any]:
    """Revierte hasta `target`. Exige `confirm: true` en el payload."""
    target = args.get('target')
    if not target:
        return {
            'command': 'downgrade',
            'status': 'error',
            'error': "Falta 'target' (ej. '-1', 'base', o una revision).",
        }
    if args.get('confirm') is not True:
        return {
            'command': 'downgrade',
            'status': 'rejected',
            'error': (
                "downgrade es destructivo — pasa 'confirm': true en args "
                'para ejecutarlo.'
            ),
        }
    cfg = build_config()
    command.downgrade(cfg, target)
    from db.commands.current import run as current_run

    return {
        'command': 'downgrade',
        'status': 'ok',
        'target': target,
        'current': current_run({}).get('current'),
    }
