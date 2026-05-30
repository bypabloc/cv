"""Paquete `models`: schema unificado (43 tablas) en SQLAlchemy 2.x.

SIN barrel: este `__init__` NO re-exporta (igual que los `__init__` de
cada dominio: auth/cv/visitor/taxonomy/i18n). Importar del MODULO concreto
para registrar solo el closure que se usa, no las 43 clases:

    from shared.db.models.auth.user import AuthUser
    from shared.db.models.cv.profile import Profile

Para el schema COMPLETO (Alembic autogenerate + seed del Lambda `db`)
usar `import shared.db.models.registry`. Ver `.claude/rules/lambda-config.md`.
"""
