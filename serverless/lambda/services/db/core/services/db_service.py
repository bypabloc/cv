"""Service de la operacion `db`: gestion del schema PostgreSQL.

Concentra la logica de negocio del Lambda `db`: construir el `Config` de
Alembic apuntando al schema unificado de `shared/db/`, e invocar los
comandos de Alembic (upgrade, downgrade, stamp, current, history)
programaticamente.

Regla de separacion:
  - controllers/db/<action>.py : orquesta (valida -> service -> normaliza).
  - services/db_service.py     : logica de negocio (este archivo).
  - utils/                     : infraestructura generica.

Alembic se invoca por API de Python, NO por subprocess: la Lambda no
tiene shell ni el binario `alembic` en el PATH (si la libreria,
empaquetada con el codigo). `DATABASE_URL` la resuelve el `env.py` de
Alembic desde el entorno (la inyecta el template SAM desde SSM).
"""

from __future__ import annotations

import io
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config


class ServiceError(Exception):
    """Error de negocio del Lambda `db`.

    El controller lo captura y lo traduce a la respuesta normalizada
    `{is_valid: False, data, code}`.
    """

    def __init__(
        self,
        message: str,
        *,
        code: int,
        error_code: str = 'SERVICE_ERROR',
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.error_code = error_code


# El modulo de schema unificado vive en `shared/db/`. Con el vendoring,
# `shared/` esta en `core/shared/`; este archivo esta en
# `core/services/`, asi que el schema esta en `../shared/db/`.
_DB_MODULE = Path(__file__).resolve().parents[1] / 'shared' / 'db'


def build_config(out: io.StringIO | None = None) -> Config:
    """Construye el `Config` de Alembic del schema unificado.

    Parameters
    ----------
    out : io.StringIO | None
        Si se pasa, Alembic escribe su salida (lo que `history` /
        `current` imprimen) a ese buffer en vez de a sys.stdout.
        `Config(stdout=...)` es la via correcta: `redirect_stdout` NO
        captura la salida de Alembic porque guarda una referencia propia
        a stdout al construir el Config.

    Returns
    -------
    Config
        Config de Alembic ligado al `alembic.ini` + `alembic/` del
        schema unificado.
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
    """Devuelve el historial completo de migraciones y la revision actual."""
    history = _capture(lambda cfg: command.history(cfg, verbose=False))
    return {
        'history': history.splitlines(),
        'current': current_revision(),
    }


# La query de listado de tablas: estimado de filas via las estadisticas
# del planner (`pg_stat_user_tables`), sin contar fila por fila.
_TABLES_QUERY = (
    "SELECT schemaname || '.' || relname AS table_name, "
    'n_live_tup AS estimated_rows '
    'FROM pg_stat_user_tables '
    'ORDER BY n_live_tup DESC'
)


def run_tables() -> dict[str, Any]:
    """Lista las tablas de la DB con un estimado de filas por tabla.

    Consulta `pg_stat_user_tables` (estadisticas del planner): `n_live_tup`
    es un estimado, NO un `COUNT(*)` exacto — barato y suficiente para una
    vista operativa. El engine SQLAlchemy se construye con la `DATABASE_URL`
    del entorno, que el handler ya resolvio con `ensure_database_url()`.

    Returns
    -------
    dict[str, Any]
        `{'tables': [{'name': str, 'rows': int}, ...]}`, ordenado por
        `rows` descendente. Lista vacia si la DB no tiene tablas de usuario.

    Raises
    ------
    ServiceError
        Si la query falla (DB inaccesible, schema sin migrar, etc.) con
        `code=5000` y `error_code='DB_QUERY_FAILED'`.
    """
    from sqlalchemy import create_engine, text

    try:
        engine = create_engine(os.environ['DATABASE_URL'], future=True)
        with engine.connect() as conn:
            rows = conn.execute(text(_TABLES_QUERY)).all()
    except Exception as exc:
        raise ServiceError(
            f'No se pudo listar las tablas: {exc}',
            code=5000,
            error_code='DB_QUERY_FAILED',
        ) from exc

    tables = [
        {'name': row.table_name, 'rows': int(row.estimated_rows)}
        for row in rows
    ]
    return {'tables': tables}


def run_seed() -> dict[str, Any]:
    """Carga data de prueba en la DB — actualmente NO disponible.

    El schema del portfolio se unifico en `shared/db/` (modelos SQLAlchemy
    + Alembic), pero NO existe todavia un seed migrado para ese schema. El
    unico seed del repo (`db/cv/seed/seed_from_yaml.py`) es legacy: apunta
    al schema viejo de `db/cv/`, depende de `psycopg` directo y de los YAML
    de `packages/content/`, y no se vendoriza con esta Lambda.

    Mientras no exista un seed para el schema unificado, esta funcion NO
    inventa data: reporta honestamente que no hay seed disponible. Cuando
    se migre el seed a `shared/db/`, esta funcion lo invocara y devolvera
    `{'seeded': True, 'statements': N}`.

    Returns
    -------
    dict[str, Any]
        `{'seeded': False, 'reason': str}` — no hay seed para el schema
        unificado todavia.
    """
    return {
        'seeded': False,
        'reason': (
            'no hay seed disponible para el schema unificado de '
            'shared/db/ — el seed legacy de db/cv/ no esta migrado'
        ),
    }
