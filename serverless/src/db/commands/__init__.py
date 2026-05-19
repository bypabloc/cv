"""@module commands — registry de comandos de la Lambda `db`.

Patron factory: cada comando es un modulo con una funcion `run(args) -> dict`.
El `handler.py` resuelve el comando del payload contra `COMMANDS` y lo
invoca. Agregar un comando = agregar un modulo + una entrada aqui (escala
sin tocar el handler).
"""

from collections.abc import Callable
from typing import Any

from db.commands import current as _current
from db.commands import downgrade as _downgrade
from db.commands import migrate as _migrate
from db.commands import show_migrations as _show
from db.commands import stamp as _stamp

# Registry {nombre de comando -> funcion run(args) -> dict}.
COMMANDS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    'migrate': _migrate.run,
    'show-migrations': _show.run,
    'current': _current.run,
    'downgrade': _downgrade.run,
    'stamp': _stamp.run,
}
