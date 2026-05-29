"""@module shared.db.warmup — precalentamiento del ORM para el cold start.

`warm_db()` crea el engine (NullPool, sin abrir conexion) y configura los
mappers SQLAlchemy de los modelos YA REGISTRADOS. Pensado para llamarse en
el module-scope (INIT) del handler de un Lambda con SnapStart: el trabajo
CPU caro (configure_mappers) queda en el SNAPSHOT y NO se paga en cada
cold/restore. El handler debe importar antes los modelos de su dominio
(`import shared.db.models.<dominio>`) para que esten registrados.

Es BEST-EFFORT: si el engine no se puede crear (ej. sin DATABASE_URL en un
test unitario) el warmup se omite silenciosamente — NUNCA rompe el INIT.
Ver `.claude/rules/lambda-config.md`.
"""

from __future__ import annotations

from shared.observability.logger import logger


def warm_db() -> None:
    """Crea el engine + configura los mappers registrados (best-effort)."""
    try:
        from sqlalchemy.orm import configure_mappers

        from shared.db.session import get_engine

        get_engine()
        configure_mappers()
    except Exception as exc:
        logger.debug('warm_db omitido: %s', type(exc).__name__)
