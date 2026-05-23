"""Service de la operacion `db`: gestion del schema PostgreSQL.

Orquestador de la logica de negocio del Lambda `db`. La operativa de
dominio (Alembic, queries SQLAlchemy) NO vive aca: se movio a
`shared.db` (`shared.db.migrations` y `shared.db.repository`). Este
service delega en esas funciones y normaliza errores a `ServiceError`,
sin importar `alembic` ni `sqlalchemy` directamente.

Regla de separacion:
  - controllers/db/<action>.py : orquesta (valida -> service -> normaliza).
  - services/db_service.py     : delega en shared.db (este archivo).
  - shared.db                  : dueno del schema, los modelos y la
                                  operativa de la DB.
"""

from __future__ import annotations

from typing import Any

from shared.db.migrations import (
    run_current as _shared_run_current,
)
from shared.db.migrations import (
    run_downgrade as _shared_run_downgrade,
)
from shared.db.migrations import (
    run_migrate as _shared_run_migrate,
)
from shared.db.migrations import (
    run_show_migrations as _shared_run_show_migrations,
)
from shared.db.migrations import (
    run_stamp as _shared_run_stamp,
)
from shared.db.repository import RepositoryError
from shared.db.repository import list_tables as _shared_list_tables


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


def run_migrate(*, target: str = 'head') -> dict[str, Any]:
    """Aplica las migraciones pendientes — delega en `shared.db`."""
    return _shared_run_migrate(target=target)


def run_downgrade(*, target: str) -> dict[str, Any]:
    """Revierte migraciones — delega en `shared.db`. Operacion destructiva."""
    return _shared_run_downgrade(target=target)


def run_stamp(*, target: str = 'head') -> dict[str, Any]:
    """Marca `target` como aplicada sin ejecutar SQL — delega en `shared.db`."""
    return _shared_run_stamp(target=target)


def run_current() -> dict[str, Any]:
    """Devuelve la revision aplicada — delega en `shared.db`."""
    return _shared_run_current()


def run_show_migrations() -> dict[str, Any]:
    """Devuelve el historial de migraciones — delega en `shared.db`."""
    return _shared_run_show_migrations()


def run_tables() -> dict[str, Any]:
    """Lista las tablas de la DB con estimado de filas.

    Delega en `shared.db.repository.list_tables` y traduce su
    `RepositoryError` al `ServiceError` que el controller espera.

    Raises
    ------
    ServiceError
        Si la query falla (DB inaccesible, schema sin migrar, etc.).
    """
    try:
        return _shared_list_tables()
    except RepositoryError as exc:
        raise ServiceError(
            exc.message,
            code=exc.code,
            error_code=exc.error_code,
        ) from exc


def run_seed() -> dict[str, Any]:
    """Carga la data del CV (YAML de `seeds/data/`) en la DB.

    Delega en `seed_service.run_seed`, que lee los YAML del CV del arbol
    del Lambda e inserta cada fila con upsert idempotente. Correr el seed
    N veces deja siempre el mismo estado.

    Returns
    -------
    dict[str, Any]
        `{'seeded': True, 'counts': {<tabla>: <filas>}}` con los conteos
        por tabla principal tras el seed.

    Raises
    ------
    ServiceError
        Si el seed falla (DB inaccesible, schema sin migrar, YAML
        invalido) con `code=5000` y `error_code='SEED_FAILED'`.
    """
    from services.seed_service import run_seed as _run_cv_seed

    try:
        return _run_cv_seed()
    except Exception as exc:
        raise ServiceError(
            f'El seed del CV fallo: {exc}',
            code=5000,
            error_code='SEED_FAILED',
        ) from exc
