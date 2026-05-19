"""@command stamp — marca una revision como aplicada SIN ejecutar el SQL.

Es el comando para adoptar Alembic en una DB que ya tiene el schema (prod):
`alembic stamp head` escribe la revision en `alembic_version` sin recrear
nada. Los datos NO se tocan.

Payload: `{"command": "stamp", "args": {"target": "head"}}`
`target` es opcional (default `head`).
"""

from typing import Any

from alembic import command

from db.alembic_runner import build_config


def run(args: dict[str, Any]) -> dict[str, Any]:
    """Marca `target` como la revision aplicada (sin ejecutar migraciones)."""
    target = args.get('target', 'head')
    cfg = build_config()
    command.stamp(cfg, target)
    from db.commands.current import run as current_run

    return {
        'command': 'stamp',
        'status': 'ok',
        'target': target,
        'current': current_run({}).get('current'),
    }
