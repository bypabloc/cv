# Lambda shared-only imports

> Los services del backend serverless del portfolio
> (`serverless/lambda/services/*`) NO importan directamente paquetes
> externos. Toda dependencia externa (pydantic, sqlalchemy, alembic,
> psycopg, boto3, botocore, aws-lambda-powertools, pydantic-settings)
> viaja por `serverless/lambda/shared/**`. Cada subpaquete shared es el
> portador unico de su paquete y lo re-exporta. El comando
> `serverless lint-deps` valida ambos contratos (dedup D-3 + imports
> shared-only) en una pasada.

## Activacion

Aplica SIEMPRE al editar, crear o refactorizar:

- Cualquier archivo `serverless/lambda/services/<X>/core/**/*.py`.
- Cualquier `serverless/lambda/services/<X>/pyproject.toml`.
- Los `__init__.py` o cualquier modulo de
  `serverless/lambda/shared/<X>/`.

NO aplica al frontend Astro ni a otros repos.

## Reglas duras (SIEMPRE / NUNCA)

- **SIEMPRE** los services importan paquetes externos como
  `from shared.<subpaquete> import <simbolo>`.
- **SIEMPRE** que aparezca un import nuevo prohibido en `core/`, ese
  paquete se re-exporta primero desde el shared portador (Fase de
  preparacion antes de migrar).
- **SIEMPRE** que un re-export nuevo se agregue, se cubre con un test
  unit en `shared/tests/unit/shared/<X>/test_<X>_reexport.py`.
- **SIEMPRE** los services declaran en `pyproject.toml` solo lo que NO
  aporta el cierre transitivo de shared (caso extremadamente raro,
  porque cada paquete tiene su shared portador definido abajo).
- **NUNCA** un archivo `services/<X>/core/**/*.py` contiene:
  - `from pydantic` / `import pydantic` / `from pydantic_settings`.
  - `from sqlalchemy` / `from sqlalchemy.dialects` / `from sqlalchemy.orm`.
  - `from alembic` / `import alembic`.
  - `import psycopg` / `from psycopg`.
  - `import boto3` / `from boto3`.
  - `import botocore` / `from botocore`.
  - `import aws_lambda_powertools` / `from aws_lambda_powertools`.
- **NUNCA** un service declara en su `pyproject.toml` deps que el
  cierre de shared ya aporta (regla D-3, validada por `serverless
  lint-deps`).
- **NUNCA** se duplica un cliente boto3 en `core/`: existe el wrapper
  en `shared.aws.<recurso>` o se agrega antes de usarlo.
- **NUNCA** atribucion de IA en codigo, commits ni docstrings.

## Catalogo de portadores

| Paquete externo | Portador shared | Como se importa en services |
|-----------------|-----------------|------------------------------|
| `pydantic` (incluye extra `[email]`) | `shared.core` | `from shared.core import BaseModel, Field, EmailStr, field_validator, model_validator, ConfigDict` |
| `pydantic_settings` | `shared.core` (declarado en `pyproject.toml`; sin re-export hoy) | Acceder via `shared.core.<algo>` o agregar re-export especifico cuando se use |
| `sqlalchemy` | `shared.db` | `from shared.db import select, func, pg_insert, Session, Base, db_session, get_engine, TimestampMixin, UUIDPKMixin` |
| `sqlalchemy.dialects.postgresql.insert` | `shared.db` | `from shared.db import pg_insert` (alias del insert postgresql) |
| `alembic` | `shared.db` (uso interno por la Lambda `db`) | n/a en services (los services no operan migrations) |
| `psycopg` | `shared.db` (uso interno via SQLAlchemy engine) | n/a en services (el engine lo crea shared.db.session) |
| `boto3` (cliente generico) | `shared.aws` | No exponemos `boto3` crudo — usar el wrapper especifico de abajo |
| `boto3.dynamodb.types.TypeDeserializer` / `TypeSerializer` | `shared.aws` | `from shared.aws import TypeDeserializer, TypeSerializer` |
| SES (boto3.client('sesv2')) | `shared.aws.ses` | `from shared.aws import send_email` (helper) o `from shared.aws import ses` (cliente module-scope) |
| DynamoDB Resource / Table | `shared.aws.dynamodb` | `from shared.aws import get_resource, get_table, reset_resource_cache` |
| SSM Parameter Store / Secrets | `shared.aws.ssm` | `from shared.aws import get_parameter, get_secret, clear_cache` |
| `aws_lambda_powertools` (logger/metrics/tracer/MetricUnit) | `shared.observability` | `from shared.observability import logger, metrics, tracer, MetricUnit` |
| HTTP responses + CORS + Turnstile | `shared.http` | `from shared.http import error_response, json_response, no_content_response, resolve_origin, verify_turnstile_token` |

## Patron correcto

```python
# services/contact_form/core/services/contact_service.py
from shared.aws import send_email
from shared.core import ApplicationError, settings
from shared.observability import MetricUnit, logger, metrics


def send_owner_email(payload: dict) -> str:
    response = send_email(
        from_address=settings.ses_from_address,
        to_addresses=payload['recipients'],
        subject=payload['subject'],
        text_body=payload['text'],
        html_body=payload['html'],
    )
    metrics.add_metric(
        name='ContactEmailSent', unit=MetricUnit.Count, value=1,
    )
    return response['MessageId']
```

## Patron incorrecto + correccion

```python
# MAL — services/contact_form/core/services/contact_service.py
import boto3
from aws_lambda_powertools.metrics import MetricUnit
from pydantic import BaseModel

# BIEN
from shared.aws import send_email
from shared.core import BaseModel
from shared.observability import MetricUnit
```

```python
# MAL — services/db/core/services/seed_service.py
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

# BIEN
from shared.db import Session, func, pg_insert as insert, select
```

## Como agregar un paquete externo nuevo al backend

1. Decidir el shared portador (aws, core, db, http, observability,
   dynamodb, cache, rate_limit). Si no encaja en ninguno, crear el
   subpaquete shared antes (con `pyproject.toml` propio y su
   `[tool.shared] internal-deps`).
2. Declarar el paquete en `[project.dependencies]` del portador.
3. Re-exportar los simbolos necesarios desde el `__init__.py` del
   portador y agregarlos a `__all__`.
4. Actualizar la tabla "Catalogo de portadores" de esta rule.
5. Si otro shared depende del nuevo, agregar a `[tool.shared]
   internal-deps` de su `pyproject.toml`.
6. Tests unit del re-export en
   `shared/tests/unit/shared/<X>/test_<paquete>_reexport.py`.
7. `python devtools/run.py serverless lint-deps` debe pasar.

## Como migrar un service que importa un paquete prohibido

1. Verificar que el paquete tiene portador shared (tabla arriba). Si
   no, primero "agregar paquete externo".
2. Reemplazar el import en `core/`:
   `from <paquete> import X` -> `from shared.<portador> import X`.
3. Si el service declara el paquete en su `pyproject.toml`, retirarlo
   (el cierre transitivo ya lo aporta). Re-sincronizar con
   `serverless tests --type=unit --lambda=<X>` que prepara el `.venv`.
4. `python devtools/run.py serverless tests --type=unit --lambda=<X>`
   verde.
5. `python devtools/run.py serverless lint-deps --lambda=<X>` exit 0
   (ambos checks: dedup + imports).

## Verificacion

```bash
python devtools/run.py serverless lint-deps                  # global
python devtools/run.py serverless lint-deps --lambda=<X>     # uno
python devtools/run.py serverless tests --type=unit          # suite
python devtools/run.py serverless tests --type=unit --shared # shared
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| `from pydantic import BaseModel` en `core/models/<X>.py` | Bypassa el portador shared | `from shared.core import BaseModel` |
| `import boto3` + `boto3.client(...)` en `core/services/` | Duplica clientes, sin singleton, sin testing centralizado | Usar/agregar wrapper en `shared.aws.<recurso>` |
| Declarar `pydantic[email]` en el `pyproject.toml` del service | Duplica con shared.core, lint-deps falla | Retirar del service; shared.core lo aporta |
| `from boto3.dynamodb.types import TypeDeserializer` | Import directo a boto3 | `from shared.aws import TypeDeserializer` |
| `from aws_lambda_powertools.metrics import MetricUnit` | Import directo a Powertools | `from shared.observability import MetricUnit` |
| `from sqlalchemy import select` en el `core/` de un service | Import directo a SQLAlchemy | `from shared.db import select` |
| Mockear `boto3.client(...)` directo en tests del service | Acopla el test al detalle de impl interna del helper | Mockear `shared.aws._client` (lazy ses) o `shared.aws.send_email` |
| Crear un re-export en shared sin tests | El cierre transitivo se rompe sin alerta | Agregar test unit del re-export en `shared/tests/unit/shared/<X>/` |
| Editar el `__init__.py` de un shared sin agregar el simbolo a `__all__` | El re-export no se expone publicamente | Agregar al `__all__` (ordenado alfabeticamente) |

## Referencias cruzadas

- `.claude/rules/lambda-controller.md` — formato general de Lambdas
  Python (operation+action, controller/service, manifest, tests).
- `.claude/docs/lambda-shared-imports/` — explicacion conceptual +
  ejemplos.
- Skill `lambda-shared-imports` — guia rapida invocable con
  `/lambda-shared-imports`.
- `serverless/lambda/shared/<X>/__init__.py` — fuente de verdad de
  los re-exports.
- `devtools/serverless/import_validator.py` — implementacion del
  check de imports.
- `devtools/serverless/dep_validator.py` — implementacion del check
  de dedup D-3.
