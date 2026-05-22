"""@module shared.db.migrations — operativa de migraciones Alembic.

Concentra la API de dominio para gestionar el schema PostgreSQL del
portfolio con Alembic: construir el `Config` apuntando al `alembic.ini`
+ `alembic/` de este subpaquete, e invocar los comandos (`upgrade`,
`downgrade`, `stamp`, `current`, `history`) por la API de Python.

Esta logica vivia en `db/core/services/db_service.py` (el Lambda `db`).
Se movio aca porque Alembic es responsabilidad de dominio de
`shared.db`: el `core/` del Lambda NO debe importar `alembic` directo,
solo consumir estas funciones (`from shared.db.migrations import ...`).

Alembic se invoca por API de Python, NO por subprocess: la Lambda no
tiene shell ni el binario `alembic` en el PATH (si la libreria,
empaquetada con el codigo). `DATABASE_URL` la resuelve el `env.py` de
Alembic desde el entorno.
"""

from __future__ import annotations

import io
from collections.abc import Callable
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config

# Raiz de este subpaquete: aqui viven `alembic.ini` y `alembic/`.
_DB_MODULE = Path(__file__).resolve().parent


def build_config(out: io.StringIO | None = None) -> Config:
    """Construye el `Config` de Alembic del schema unificado.

    Parameters
    ----------
    out : io.StringIO | None
        Si se pasa, Alembic escribe su salida (lo que `history` /
        `current` imprimen) a ese buffer en vez de a `sys.stdout`.
        `Config(stdout=...)` es la via correcta: `redirect_stdout` NO
        captura la salida de Alembic porque guarda una referencia propia
        a stdout al construir el `Config`.

    Returns
    -------
    Config
        `Config` de Alembic ligado al `alembic.ini` + `alembic/` de
        `shared/db/`.
    """
    cfg = Config(
        str(_DB_MODULE / 'alembic.ini'),
        stdout=out if out is not None else io.StringIO(),
    )
    cfg.set_main_option('script_location', str(_DB_MODULE / 'alembic'))
    return cfg


def _capture(fn: Callable[[Config], None]) -> str:
    """Ejecuta un comando de Alembic capturando lo que imprime.

    `fn` recibe un `Config` ligado a un buffer y debe invocar el comando
    Alembic con el. Retorna el texto capturado.
    """
    buffer = io.StringIO()
    cfg = build_config(out=buffer)
    fn(cfg)
    return buffer.getvalue().strip()


def current_revision() -> str | None:
    """Devuelve la revision de Alembic aplicada actualmente en la DB.

    Returns
    -------
    str | None
        La revision actual, o None si la DB esta sin migrar.
    """
    output = _capture(lambda cfg: command.current(cfg))
    return output or None


def run_migrate(*, target: str = 'head') -> dict[str, Any]:
    """Aplica las migraciones pendientes (`alembic upgrade`).

    Parameters
    ----------
    target : str
        Revision destino (default `head`).

    Returns
    -------
    dict[str, Any]
        Resultado con `target` aplicado y la `current` resultante.
    """
    cfg = build_config()
    command.upgrade(cfg, target)
    return {'target': target, 'current': current_revision()}


def run_downgrade(*, target: str) -> dict[str, Any]:
    """Revierte migraciones (`alembic downgrade`). Operacion destructiva.

    Parameters
    ----------
    target : str
        Revision destino (`-1`, `base`, o una revision).

    Returns
    -------
    dict[str, Any]
        Resultado con `target` aplicado y la `current` resultante.
    """
    cfg = build_config()
    command.downgrade(cfg, target)
    return {'target': target, 'current': current_revision()}


def run_stamp(*, target: str = 'head') -> dict[str, Any]:
    """Marca `target` como revision aplicada SIN ejecutar el SQL.

    Es el comando para adoptar Alembic en una DB que ya tiene el schema
    (prod): escribe la revision en `alembic_version` sin recrear nada.

    Parameters
    ----------
    target : str
        Revision a marcar (default `head`).

    Returns
    -------
    dict[str, Any]
        Resultado con `target` aplicado y la `current` resultante.
    """
    cfg = build_config()
    command.stamp(cfg, target)
    return {'target': target, 'current': current_revision()}


def run_current() -> dict[str, Any]:
    """Devuelve la revision de Alembic aplicada actualmente."""
    return {'current': current_revision()}


def run_show_migrations() -> dict[str, Any]:
    """Devuelve el historial de migraciones y la revision actual."""
    history = _capture(lambda cfg: command.history(cfg, verbose=False))
    return {
        'history': history.splitlines(),
        'current': current_revision(),
    }
