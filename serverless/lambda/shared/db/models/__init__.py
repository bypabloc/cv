"""Paquete `models`: schema unificado (43 tablas) en SQLAlchemy 2.x.

SIN barrel: este `__init__` NO re-exporta. Importar del dominio puntual
para no registrar las 43 clases cuando solo se usan unas pocas:

    from shared.db.models.auth import AuthUser
    from shared.db.models.cv import Profile

Para el schema COMPLETO (Alembic autogenerate + seed del Lambda `db`)
usar `import shared.db.models.registry`. Ver `.claude/rules/lambda-config.md`.
"""
