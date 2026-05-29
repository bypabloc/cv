"""Subpaquete `core`: Primitivos compartidos: config, excepciones, tipos, ulid, pydantic.

Subpaquete SIN barrel: este `__init__` NO re-exporta nada. Importar
SIEMPRE del modulo concreto (contrato `.claude/rules/lambda-shared-imports.md`):

    from shared.core.exceptions import ValidationError
    from shared.core.pydantic_types import BaseModel, Field
"""
