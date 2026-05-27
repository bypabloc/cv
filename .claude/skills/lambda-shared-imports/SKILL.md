---
name: lambda-shared-imports
description: >
  Catalog of which shared subpackage carries each external package
  (pydantic, sqlalchemy, boto3, aws-lambda-powertools, ...) in the
  portfolio's serverless backend. The services NEVER import these
  packages directly in `core/`. Use when the user says "donde vive
  pydantic", "como importar boto3 en el lambda", "portador shared",
  "shared-only imports", "shared only", "como agregar paquete shared",
  "where does pydantic live", "where to import boto3", "shared
  subpackage", "lint-deps fails on imports", "shared-only contract",
  "lambda imports", "EmailStr en lambda", "como migrar un import
  prohibido", "MetricUnit en el handler", or asks about the import
  contract of the serverless services.
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "opcional: nombre del paquete externo a buscar"
---

# Lambda shared-only imports — guia rapida

Los services del backend serverless del portfolio
(`serverless/lambda/services/*`) NO importan directamente paquetes
externos. Toda dependencia externa viaja por
`serverless/lambda/shared/**`. Cada subpaquete shared es el portador
unico de su paquete.

## Catalogo de portadores

| Paquete externo | Portador shared | Import en services |
|-----------------|-----------------|---------------------|
| `pydantic` (con extra `[email]`) | `shared.core` | `from shared.core import BaseModel, Field, EmailStr, field_validator, model_validator, ConfigDict` |
| `pydantic_settings` | `shared.core` (declarado, sin re-export) | acceder al modulo o agregar re-export cuando se use |
| `sqlalchemy` (`select`, `func`, `Session`) | `shared.db` | `from shared.db import select, func, Session, Base, db_session` |
| `sqlalchemy.dialects.postgresql.insert` | `shared.db` | `from shared.db import pg_insert` |
| `alembic` | `shared.db` (uso interno) | n/a |
| `psycopg` | `shared.db` (uso interno) | n/a |
| `boto3` (cliente generico) | `shared.aws` | usar wrapper especifico (abajo) |
| `boto3.dynamodb.types.TypeDeserializer` | `shared.aws` | `from shared.aws import TypeDeserializer, TypeSerializer` |
| SES (boto3.client('sesv2')) | `shared.aws.ses` | `from shared.aws import send_email` |
| DynamoDB Resource | `shared.aws.dynamodb` | `from shared.aws import get_resource, get_table` |
| SSM Parameter Store | `shared.aws.ssm` | `from shared.aws import get_parameter, get_secret` |
| `aws_lambda_powertools` | `shared.aws`, `shared.observability` | `from shared.observability import logger, metrics, tracer, MetricUnit` |

## Procedimiento: agregar paquete externo nuevo

1. Decidir el shared portador (aws/core/db/http/observability/...).
2. Declarar el paquete en `[project.dependencies]` del portador
   (`serverless/lambda/shared/<X>/pyproject.toml`).
3. Re-exportar los simbolos en `__init__.py` y agregar a `__all__`.
4. Test unit del re-export en
   `serverless/lambda/shared/tests/unit/shared/<X>/`.
5. `python devtools/run.py serverless lint-deps` verde.

## Procedimiento: migrar un service con import prohibido

1. Cambiar el import en `core/`:
   `from <paquete> import X` -> `from shared.<portador> import X`.
2. Si el service declara el paquete en su `pyproject.toml`, retirarlo
   (el cierre transitivo ya lo aporta).
3. `python devtools/run.py serverless tests --type=unit --lambda=<X>`.
4. `python devtools/run.py serverless lint-deps --lambda=<X>`.

## Patron correcto

```python
from shared.aws import send_email
from shared.core import BaseModel, EmailStr, Field
from shared.db import Session, func, pg_insert as insert, select
from shared.observability import MetricUnit, logger, metrics
```

## Patron incorrecto

```python
from pydantic import BaseModel               # MAL
from sqlalchemy import select                # MAL
import boto3                                  # MAL
from aws_lambda_powertools.metrics import MetricUnit  # MAL
```

## Verificacion automatica

`python devtools/run.py serverless lint-deps` corre dos checks:

1. **Dedup D-3**: el `pyproject.toml` del lambda no declara deps que ya
   aporta el cierre de shared.
2. **Imports shared-only**: AST scan de `services/<X>/core/**/*.py`
   detecta imports directos a paquetes prohibidos.

Exit 1 si cualquiera falla. Reporte CLI muestra archivo:linea + paquete.

## Referencia

- Rule autoritativa: `.claude/rules/lambda-shared-imports.md`.
- Docs conceptual: `.claude/docs/lambda-shared-imports/`.
- Implementacion del check: `devtools/serverless/import_validator.py`.
- Formato Lambda general: `.claude/rules/lambda-controller.md`.
