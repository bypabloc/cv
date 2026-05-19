"""@command show-migrations — historial de migraciones + revision actual.

Payload: `{"command": "show-migrations"}`
"""

from typing import Any

from alembic import command

from db.alembic_runner import capture


def run(_args: dict[str, Any]) -> dict[str, Any]:
    """Devuelve el historial completo de migraciones y la revision actual."""
    # Cada `capture` arma su propio Config ligado a un buffer y lo pasa al
    # callback. `history` / `current` deben usar ESE Config.
    history = capture(lambda cfg: command.history(cfg, verbose=False))
    current = capture(lambda cfg: command.current(cfg))
    return {
        'command': 'show-migrations',
        'status': 'ok',
        'history': history.splitlines(),
        'current': current or None,
    }
