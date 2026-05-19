"""@module db_url — resuelve la connection string del CV.

La URL NUNCA se hardcodea. Se resuelve de la env var `CV_DATABASE_URL`
(mismo contrato que `alembic/env.py`). En el flujo real se exporta
puntualmente desde SSM antes de invocar el seed:

    CV_DATABASE_URL="$(...)" python seed/seed_from_yaml.py
"""

import os


def get_database_url() -> str:
    """Devuelve `CV_DATABASE_URL` o falla con un mensaje accionable.

    Acepta tanto `postgresql://` como `postgresql+psycopg://`. El seed usa
    `psycopg` directo, asi que normaliza al esquema sin el driver de
    SQLAlchemy.
    """
    url = os.environ.get('CV_DATABASE_URL')
    if not url:
        raise RuntimeError(
            'CV_DATABASE_URL no esta seteada. Exportala apuntando al Neon '
            'del portfolio antes de correr el seed (ver db/cv/README.md).'
        )
    return url.replace('postgresql+psycopg://', 'postgresql://', 1)
