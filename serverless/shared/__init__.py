"""
Libreria comun del backend serverless del portfolio.

Este paquete NO re-exporta nada: cada subpaquete es la unidad de import.
Importar SIEMPRE de forma explicita desde el subpaquete correspondiente:

    from shared.core.exceptions import ValidationError
    from shared.aws.dynamodb import get_table
    from shared.observability.logger import logger
    from shared.http.responses import json_response

Subpaquetes:
- `core`          — config, excepciones, tipos, ulid (primitivos sin deps).
- `aws`           — clientes boto3: DynamoDB, SES, SSM.
- `observability` — logger, tracer, metrics (Powertools v3).
- `http`          — CORS, responses, ip_extractor, turnstile, validators.
- `db`            — ORM SQLAlchemy + Alembic para Neon PostgreSQL.
- `dynamodb`      — ORM minimalista para DynamoDB (modelos Pydantic).
- `cache`         — cache DynamoDB con TTL, SWR y lock distribuido.
- `rate_limit`    — rate-limit per-IP sliding window weighted.

Cada subpaquete declara sus dependencias externas e internas en su propio
`pyproject.toml`. devtools resuelve por AST que subpaquetes usa cada
Lambda y vendoriza solo ese cierre transitivo.
"""
