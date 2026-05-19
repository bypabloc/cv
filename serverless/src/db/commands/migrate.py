"""@command migrate — aplica las migraciones pendientes (`alembic upgrade`).

Payload: `{"command": "migrate", "args": {"target": "head"}}`
`target` es opcional (default `head`).
"""

from typing import Any

from alembic import command

from db.alembic_runner import build_config


def run(args: dict[str, Any]) -> dict[str, Any]:
    """Aplica las migraciones hasta `target` (default `head`)."""
    target = args.get('target', 'head')
    cfg = build_config()
    command.upgrade(cfg, target)
    # Tras el upgrade, reporta la revision en la que quedo la DB.
    from db.commands.current import run as current_run

    return {
        'command': 'migrate',
        'status': 'ok',
        'target': target,
        'current': current_run({}).get('current'),
    }
