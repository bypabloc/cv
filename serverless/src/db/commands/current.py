"""@command current — revision de Alembic aplicada actualmente en la DB.

Payload: `{"command": "current"}`
"""

from typing import Any

from alembic import command

from db.alembic_runner import capture


def run(_args: dict[str, Any]) -> dict[str, Any]:
    """Devuelve la revision actual de la DB (None si esta sin migrar)."""
    # `capture` construye el Config ligado a un buffer y se lo pasa al
    # callback — `command.current` debe recibir ESE Config, no otro.
    output = capture(lambda cfg: command.current(cfg))
    return {
        'command': 'current',
        'status': 'ok',
        # `alembic current` imprime la revision (o vacio si no hay ninguna).
        'current': output or None,
    }
