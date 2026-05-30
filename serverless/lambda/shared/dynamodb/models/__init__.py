"""Modelos del ORM DynamoDB: uno por tabla del backend serverless.

Cada modelo es una subclase de `shared.dynamodb.base.BaseModel` con un
`Meta: TableMeta` que declara claves, TTL y GSIs.

Vaciado a proposito: sin re-exports (no-barrel). Los consumidores
importan del modulo concreto (`from shared.db.models.<dom>.<mod>
import <Clase>`). Lo enforza el conformance `serverless lint-deps`.
Ver `.claude/rules/lambda-shared-imports.md`.
"""
