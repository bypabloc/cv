"""@module url — resolucion de la connection string PostgreSQL.

Fuente unica de la `DATABASE_URL` para todo lo que toca la DB del portfolio:
el engine de `session.py`, el `env.py` de Alembic y la Lambda `db`.

Orden de precedencia:
1. `DATABASE_URL` ya en el entorno (uso local / CI / tests) — se respeta.
2. Si no, se resuelve el parametro SSM apuntado por `SSM_NEON_URL_PATH`
   (KMS decrypt + cache Powertools) — es lo que pasa en las Lambdas, donde
   el template SAM inyecta el path del parametro, no el valor.

La URL se normaliza al driver `psycopg` v3 (`postgresql+psycopg://`), el
unico instalado en el Layer. NUNCA se logea el valor — solo el path SSM.
"""

import os


def _normalize(url: str) -> str:
    """Normaliza la URL al driver psycopg v3 que usa SQLAlchemy."""
    if url.startswith('postgresql://'):
        return url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return url


def resolve_database_url() -> str:
    """Devuelve la connection string lista para SQLAlchemy.

    Raises:
        RuntimeError: si ni `DATABASE_URL` ni `SSM_NEON_URL_PATH` estan
        seteadas.
    """
    url = os.environ.get('DATABASE_URL')
    if url:
        return _normalize(url)

    ssm_path = os.environ.get('SSM_NEON_URL_PATH')
    if not ssm_path:
        raise RuntimeError(
            'Ni DATABASE_URL ni SSM_NEON_URL_PATH estan seteadas. En las '
            'Lambdas el template SAM inyecta SSM_NEON_URL_PATH; en local '
            'exporta DATABASE_URL (ver .claude/rules/neon-management.md).'
        )

    # Import tardio: aws.ssm arrastra boto3/Powertools — innecesario en
    # el camino local donde DATABASE_URL ya viene seteada.
    from shared.aws.ssm import get_secret

    return _normalize(get_secret(ssm_path))


def ensure_database_url() -> None:
    """Garantiza `DATABASE_URL` en el entorno (para consumidores que la leen
    directo, como el `env.py` de Alembic). Idempotente.
    """
    if not os.environ.get('DATABASE_URL'):
        os.environ['DATABASE_URL'] = resolve_database_url()
