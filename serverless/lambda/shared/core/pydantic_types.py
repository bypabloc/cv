"""@module shared.core.pydantic_types — portador de los primitivos pydantic.

Los `core/` de los services importan pydantic SOLO desde aca (contrato
`.claude/rules/lambda-shared-imports.md`): NUNCA `from pydantic` directo.
Modulo concreto (no barrel) — importar `from shared.core.pydantic_types
import BaseModel, Field`.
"""

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

__all__ = [
    'BaseModel',
    'ConfigDict',
    'EmailStr',
    'Field',
    'field_validator',
    'model_validator',
]
