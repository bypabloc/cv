"""@module session — engine SQLAlchemy + sessionmaker para las Lambdas.

El engine se crea UNA vez a module-scope y se reutiliza entre invocaciones
warm de la misma Lambda (mismo patron que el `pg_writer.py` original cacheaba
la conexion psycopg). El cold start paga la creacion del engine; las
invocaciones siguientes la reusan.

La connection string la resuelve `_shared.db.url.resolve_database_url`
(`DATABASE_URL` del entorno, o SSM via `SSM_NEON_URL_PATH`). NUNCA se
hardcodea.

`NullPool`: en Lambda no se mantiene un pool de conexiones entre
invocaciones distintas — cada contenedor maneja una invocacion a la vez y
Neon tiene su propio pooler upstream. Una conexion por engine, reciclada.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .url import resolve_database_url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Engine SQLAlchemy cacheado a module-scope (reusado entre invocaciones
    warm de la Lambda). `lru_cache` garantiza una sola instancia.
    """
    from sqlalchemy.pool import NullPool

    return create_engine(
        resolve_database_url(),
        poolclass=NullPool,
        future=True,
    )


@lru_cache(maxsize=1)
def _session_factory() -> sessionmaker[Session]:
    """`sessionmaker` cacheado, ligado al engine module-scope."""
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


@contextmanager
def db_session() -> Iterator[Session]:
    """Context manager de Session: commit al salir limpio, rollback ante
    excepcion, close siempre.

    Uso en una Lambda:

        from _shared.db.session import db_session
        from _shared.db.models import Contact

        with db_session() as session:
            session.add(Contact(...))
    """
    session = _session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
