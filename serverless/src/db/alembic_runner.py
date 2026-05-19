"""@module alembic_runner — wrapper de Alembic para la Lambda `db`.

Centraliza la construccion del `alembic.config.Config` apuntando al modulo
unificado `_shared/db/alembic`. Los comandos (`commands/*`) invocan Alembic
programaticamente via este modulo — no via subprocess (la Lambda no tiene
shell ni el binario `alembic` en el PATH; si la libreria, empaquetada con
el codigo de la Lambda).

`DATABASE_URL` la resuelve el `env.py` de Alembic desde el entorno (la
inyecta el template SAM desde SSM).
"""

import io
from collections.abc import Callable
from pathlib import Path

from alembic.config import Config

# La Lambda `db` empaqueta `serverless/src/`; el modulo de schema vive en
# `_shared/db/`. La config de Alembic apunta a su `alembic.ini` + `alembic/`.
_DB_MODULE = Path(__file__).resolve().parent.parent / '_shared' / 'db'


def build_config(out: io.StringIO | None = None) -> Config:
    """Construye el `Config` de Alembic del schema unificado.

    `out`: si se pasa, Alembic escribe su salida (lo que `history` /
    `current` imprimen) a ese buffer en vez de a sys.stdout.
    `Config(stdout=...)` es la via correcta — `redirect_stdout` NO captura la
    salida de Alembic porque Alembic guarda una referencia propia a stdout al
    construir el Config.
    """
    cfg = Config(
        str(_DB_MODULE / 'alembic.ini'),
        stdout=out if out is not None else io.StringIO(),
    )
    cfg.set_main_option('script_location', str(_DB_MODULE / 'alembic'))
    return cfg


def capture(fn: Callable[[Config], None]) -> str:
    """Ejecuta un comando de Alembic capturando lo que imprime.

    `fn` recibe un `Config` ligado a un buffer y debe invocar el comando
    Alembic con el. Retorna el texto capturado.

    Ejemplo:
        text = capture(lambda cfg: command.current(cfg))
    """
    buffer = io.StringIO()
    cfg = build_config(out=buffer)
    fn(cfg)
    return buffer.getvalue().strip()
