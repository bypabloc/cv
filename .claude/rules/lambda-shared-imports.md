# Lambda shared-only imports

> Los services del backend serverless del portfolio
> (`serverless/lambda/services/*`) NO importan directamente paquetes
> externos. Toda dependencia externa (pydantic, sqlalchemy, alembic,
> psycopg, boto3, botocore, aws-lambda-powertools, pydantic-settings)
> viaja por `serverless/lambda/shared/**`. Cada subpaquete shared es el
> portador unico de su paquete, en un **modulo concreto** (los `__init__.py`
> de `shared/*` estan VACIOS: cero re-exports/barrels). Se importa SIEMPRE
> del modulo concreto, NUNCA del barrel ni el submodulo-objeto. El comando
> `serverless lint-deps` valida 3 contratos (dedup D-3 + imports shared-only
> + no-submodule) en una pasada.

## Activacion

Aplica SIEMPRE al editar, crear o refactorizar:

- Cualquier archivo `serverless/lambda/services/<X>/core/**/*.py`.
- Cualquier `serverless/lambda/services/<X>/pyproject.toml`.
- Los `__init__.py` o cualquier modulo de
  `serverless/lambda/shared/<X>/`.

NO aplica al frontend Astro ni a otros repos.

## Reglas duras (SIEMPRE / NUNCA)

- **SIEMPRE** los services importan paquetes externos desde el MODULO
  concreto del portador: `from shared.<subpaquete>.<modulo> import
  <simbolo>` (ej. `from shared.aws.ssm import get_secret`). Los paquetes
  externos sin modulo de dominio propio tienen un portador dedicado:
  pydantic -> `shared.core.pydantic_types`; sqlalchemy (select/func/
  delete/pg_insert/Session) -> `shared.db.sa`; MetricUnit ->
  `shared.observability.metrics`.
- **SIEMPRE** los modelos SQLAlchemy se importan por DOMINIO:
  `from shared.db.models.auth import AuthUser` (NUNCA del barrel
  `shared.db.models`, vacio). El "cargar todo" para Alembic/seed es
  `import shared.db.models.registry`.
- **SIEMPRE** que aparezca un import nuevo prohibido en `core/`, se agrega
  el paquete a un modulo concreto del shared portador (en su pyproject +
  un re-export en el modulo, NO en el `__init__`).
- **SIEMPRE** los `__init__.py` de `shared/*` quedan VACIOS (docstring-only).
- **SIEMPRE** que un re-export nuevo se agregue, se cubre con un test
  unit en `shared/tests/unit/shared/<X>/`.
- **SIEMPRE** los services declaran en `pyproject.toml` solo lo que NO
  aporta el cierre transitivo de shared.
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
- **NUNCA** importar un SUBMODULO de shared via su barrel con `from`:
  `from shared.auth import webauthn` esta PROHIBIDO. Usar el simbolo
  concreto (`from shared.auth.webauthn import WebauthnCloneError`) o, si se
  necesita el objeto-modulo (monkeypatch en tests, import con efecto
  secundario), `import shared.auth.webauthn as webauthn`. Lo enforza el
  check no-submodule (`serverless lint-deps`, Check 3) sobre TODO
  `serverless/lambda/**` (services + shared + tests).
- **NUNCA** re-exportar en el `__init__.py` de un subpaquete de `shared/`
  (deben estar vacios: cero barrels).
- **NUNCA** atribucion de IA en codigo, commits ni docstrings.

## Catalogo de portadores

| Paquete externo | Portador shared | Como se importa en services |
|-----------------|-----------------|------------------------------|
| `pydantic` (incluye extra `[email]`) | `shared.core` | `from shared.core import BaseModel, Field, EmailStr, field_validator, model_validator, ConfigDict` |
| `pydantic_settings` | `shared.core` (declarado en `pyproject.toml`; sin re-export hoy) | Acceder via `shared.core.<algo>` o agregar re-export especifico cuando se use |
| `sqlalchemy` (select/func/delete/Session) | `shared.db.sa` | `from shared.db.sa import select, func, delete, Session` |
| `sqlalchemy.dialects.postgresql.insert` | `shared.db.sa` | `from shared.db.sa import pg_insert` (alias del insert postgresql) |
| `sqlalchemy` Base / mixins | `shared.db.base` | `from shared.db.base import Base, TimestampMixin, UUIDPKMixin` |
| engine / Session factory | `shared.db.session` | `from shared.db.session import db_session, get_engine` |
| `alembic` | `shared.db.migrations` (solo Lambda `db`) | `from shared.db.migrations import run_migrate, ...` (services no migran) |
| `psycopg` | `shared.db.session` (uso interno) | n/a en services (el engine lo crea shared.db.session) |
| `boto3` (cliente generico) | `shared.aws.*` | No exponemos `boto3` crudo — usar el wrapper especifico de abajo |
| `boto3.dynamodb.types.TypeDeserializer` / `TypeSerializer` | `shared.aws.dynamodb_types` | `from shared.aws.dynamodb_types import TypeDeserializer, TypeSerializer` |
| SES (boto3.client('sesv2')) | `shared.aws.ses` | `from shared.aws.ses import send_email` (helper); `import shared.aws.ses` para el cliente `ses` lazy |
| DynamoDB Resource / Table | `shared.aws.dynamodb` | `from shared.aws.dynamodb import get_resource, get_table, reset_resource_cache` |
| SSM Parameter Store / Secrets | `shared.aws.ssm` | `from shared.aws.ssm import get_parameter, get_secret, get_secret_by_name, clear_cache` |
| `aws_lambda_powertools` (logger) | `shared.observability.logger` | `from shared.observability.logger import logger` |
| `aws_lambda_powertools` (metrics + MetricUnit) | `shared.observability.metrics` | `from shared.observability.metrics import metrics, MetricUnit` (X-Ray eliminado: sin tracer) |
| HTTP responses / CORS / Turnstile | `shared.http.{responses,cors,turnstile}` | `from shared.http.responses import json_response`; `from shared.http.cors import resolve_origin`; `from shared.http.turnstile import verify_turnstile_token` |
| `pyotp` (TOTP RFC 6238) | `shared.auth.totp` | `from shared.auth.totp import generate_totp_secret_b32, verify_totp_code, build_otpauth_url` |
| `fido2` (python-fido2, WebAuthn) | `shared.auth.webauthn` | `from shared.auth.webauthn import build_register_options, verify_authentication, build_login_options, WebauthnCloneError` |
| KMS (`boto3.client('kms')`, Encrypt/Decrypt CMK directa) | `shared.aws.kms` | `from shared.aws.kms import kms_encrypt, kms_decrypt` |

## Patron correcto

```python
# services/contact_form/core/services/contact_service.py
from shared.aws.ses import send_email
from shared.core.config import settings
from shared.core.exceptions import ApplicationError
from shared.observability.logger import logger
from shared.observability.metrics import MetricUnit, metrics


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
from shared.aws import send_email          # barrel vacio -> ImportError
from shared.auth import webauthn           # submodulo via barrel -> lint-deps FAIL

# BIEN — modulo concreto
from shared.aws.ses import send_email
from shared.core.pydantic_types import BaseModel
from shared.observability.metrics import MetricUnit
from shared.auth.webauthn import WebauthnCloneError  # simbolo, no el submodulo
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
