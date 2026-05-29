"""Subpaquete `db`: ORM SQLAlchemy + Alembic del schema PostgreSQL (Neon).

Subpaquete SIN barrel: este `__init__` NO re-exporta nada. Importar
SIEMPRE del modulo concreto (contrato `.claude/rules/lambda-shared-imports.md`):

    from shared.db.session import db_session, get_engine
    from shared.db.sa import select, func, pg_insert, Session
    from shared.db.models.auth import AuthUser
"""
