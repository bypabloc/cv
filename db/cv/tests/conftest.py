"""@module conftest — fixtures de los tests del schema del CV.

Los tests corren contra una DB PostgreSQL real (un branch Neon efimero o un
Postgres local) — un test de schema mockeado no probaria el schema. La
connection string se resuelve de `CV_DATABASE_URL`; si no esta seteada, los
tests se omiten (skip) en vez de fallar.

Pre-condicion: el schema debe estar aplicado (`alembic upgrade head`) y el
seed ejecutado (`python seed/seed_from_yaml.py`) antes de correr la suite.
"""

from collections.abc import Iterator
import os
from pathlib import Path
import sys

import psycopg
import pytest


# El seed vive en db/cv/seed; los tests en db/cv/tests. Agrega db/cv al path
# para poder importar `seed.*` si algun test lo necesita.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _database_url() -> str | None:
    """URL de la DB de test, normalizada al esquema de psycopg."""
    url = os.environ.get('CV_DATABASE_URL')
    if not url:
        return None
    return url.replace('postgresql+psycopg://', 'postgresql://', 1)


@pytest.fixture(scope='session')
def db_url() -> str:
    """Connection string de la DB de test. Skip si no esta configurada."""
    url = _database_url()
    if not url:
        pytest.skip(
            'CV_DATABASE_URL no seteada — los tests de schema necesitan '
            'una DB real (branch Neon efimero).'
        )
    return url


@pytest.fixture
def conn(db_url: str) -> Iterator[psycopg.Connection]:
    """Conexion psycopg de solo lectura para inspeccionar el schema/data."""
    with psycopg.connect(db_url) as connection:
        yield connection
