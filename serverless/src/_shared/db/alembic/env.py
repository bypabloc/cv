"""Alembic env — schema unificado del portfolio.

`target_metadata` es `_shared.db.Base.metadata` (las 35 tablas: datos del
visitante + contenido del CV). Habilita `alembic revision --autogenerate`.

La connection string la resuelve `_shared.db.url.resolve_database_url`
(`DATABASE_URL` del entorno, o SSM via `SSM_NEON_URL_PATH`). NUNCA se
hardcodea.

Este Alembic gestiona TODO el schema PostgreSQL del portfolio — es la unica
fuente de verdad. La tabla de versiones es la estandar `alembic_version`.

`include_name` excluye dos objetos del autogenerate:
- `schema_migrations`: la tabla del runner SQL viejo, aun presente en prod
  durante la transicion. NO la gestiona Alembic; se elimina en una
  migracion explicita.
- `tracking_events_default`: particion de `tracking_events`, no una tabla
  autogestionada — la crea la migracion con op.execute().
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# El directorio alembic/ debe estar en el path: los scripts de migracion
# importan `_init_schema_extras` (piezas que Alembic no autogenera).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import _shared.db.models  # noqa: F401  -- puebla Base.metadata
from _shared.db import Base
from _shared.db.url import resolve_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Objetos que el autogenerate NO debe tocar (ver docstring del modulo).
_IGNORED_TABLES = {'schema_migrations', 'tracking_events_default'}


def _include_name(
    name: str | None, type_: str, _parent_names: dict
) -> bool:
    """Filtra que tablas refleja Alembic."""
    if type_ == 'table':
        return name not in _IGNORED_TABLES
    return True


def run_migrations_offline() -> None:
    """Migraciones en modo offline: emite el SQL sin conectar a la DB."""
    context.configure(
        url=resolve_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        compare_type=True,
        compare_server_default=True,
        include_name=_include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Migraciones en modo online: conecta a la DB y aplica."""
    section = config.get_section(config.config_ini_section, {})
    section['sqlalchemy.url'] = resolve_database_url()
    connectable = engine_from_config(
        section,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_name=_include_name,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
