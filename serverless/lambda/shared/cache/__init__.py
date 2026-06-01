"""Subpaquete `cache`: Cache DynamoDB con TTL, SWR y lock distribuido.

Subpaquete SIN barrel: este `__init__` NO re-exporta nada. Importar
SIEMPRE del modulo concreto (contrato `.claude/rules/lambda-shared-imports.md`):

    from shared.cache.decorator import cached
    from shared.cache.client import DynamoDBCache
"""
