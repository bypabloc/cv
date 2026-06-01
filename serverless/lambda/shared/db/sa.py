"""@module shared.db.sa — portador de los primitivos SQLAlchemy.

Los `core/` de los services + los repos importan los constructos SQLAlchemy
de uso comun (select/func/delete + el insert del dialecto postgresql + la
Session del ORM) SOLO desde aca (contrato
`.claude/rules/lambda-shared-imports.md`): NUNCA `from sqlalchemy` directo
en services. Modulo concreto (no barrel) — importar `from shared.db.sa
import select, func, pg_insert, Session`.
"""

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

__all__ = [
    'Session',
    'delete',
    'func',
    'pg_insert',
    'select',
]
