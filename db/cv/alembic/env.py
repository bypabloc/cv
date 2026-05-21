"""Alembic env — schema del CV.

`target_metadata` es `models.Base.metadata` (todas las tablas del CV), lo
que habilita `alembic revision --autogenerate`.

La connection string se resuelve desde la env var `CV_DATABASE_URL` (NUNCA
hardcodeada). En el flujo real se exporta puntualmente desde SSM:

    CV_DATABASE_URL="$(...)" alembic upgrade head

`version_table='cv_alembic_version'` aisla el registro de versiones del CV
del runner SQL del backend serverless (que usa `schema_migrations`).
"""

from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from models import Base


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

VERSION_TABLE = 'cv_alembic_version'

# Tablas que SI gestiona este Alembic: solo las del CV (las de
# `Base.metadata`) + su propia tabla de versiones. Critico: el CV comparte
# el schema `public` con el backend serverless (`contacts`,
# `tracking_events`, ...). Sin este filtro, el autogenerate veria esas
# tablas como "removidas" y generaria `DROP TABLE` destructivos.
_CV_TABLES = set(target_metadata.tables.keys()) | {VERSION_TABLE}


def _include_name(name: str | None, type_: str, _parent_names: dict) -> bool:
    """Filtra que objetos refleja Alembic. A nivel `table`, solo deja pasar
    las tablas del CV — el resto del schema `public` se ignora por completo.
    """
    if type_ == 'table':
        return name in _CV_TABLES
    return True


def _include_object(
    obj: object,
    _name: str | None,
    type_: str,
    _reflected: bool,
    _compare: object,
) -> bool:
    """Defensa adicional: nunca emite cambios sobre una tabla ajena al CV
    (cubre indices/constraints que `include_name` no alcanza a filtrar).
    """
    if type_ == 'table':
        return getattr(obj, 'name', None) in _CV_TABLES
    parent = getattr(obj, 'table', None)
    if parent is not None:
        return getattr(parent, 'name', None) in _CV_TABLES
    return True


def _database_url() -> str:
    """Resuelve la URL de la DB desde el entorno. Falla si no esta seteada."""
    url = os.environ.get('CV_DATABASE_URL')
    if not url:
        raise RuntimeError(
            'CV_DATABASE_URL no esta seteada. Exportala apuntando al Neon '
            'del portfolio antes de correr alembic '
            '(ver db/cv/README.md).'
        )
    return url


def run_migrations_offline() -> None:
    """Migraciones en modo offline: emite el SQL sin conectar a la DB."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        version_table=VERSION_TABLE,
        compare_type=True,
        compare_server_default=True,
        include_name=_include_name,
        include_object=_include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Migraciones en modo online: conecta a la DB y aplica."""
    section = config.get_section(config.config_ini_section, {})
    section['sqlalchemy.url'] = _database_url()
    connectable = engine_from_config(
        section,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table=VERSION_TABLE,
            compare_type=True,
            compare_server_default=True,
            include_name=_include_name,
            include_object=_include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
