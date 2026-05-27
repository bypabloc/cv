# Portadores shared

> Catalogo completo de subpaquetes shared del backend serverless del
> portfolio y que paquetes externos absorben. Fuente de verdad: los
> `__init__.py` y `pyproject.toml` de cada subpaquete bajo
> `serverless/lambda/shared/<X>/`.

## Tabla resumen

| Subpaquete shared | Paquetes externos que aporta | Re-exporta |
|-------------------|------------------------------|-------------|
| `shared.core` | `pydantic[email]`, `pydantic_settings` | `BaseModel`, `Field`, `EmailStr`, `field_validator`, `model_validator`, `ConfigDict` + tipos del dominio (`Settings`, `ApplicationError`, ...) |
| `shared.db` | `sqlalchemy`, `alembic`, `psycopg[binary]` | `select`, `func`, `pg_insert` (postgresql), `Session`, `Base`, `db_session`, `get_engine`, helpers del repository |
| `shared.aws` | `boto3`, `aws-lambda-powertools[all]` | `get_resource`, `get_table`, `ses`, `send_email`, `TypeDeserializer`, `TypeSerializer`, `get_parameter`, `get_secret`, `clear_cache` |
| `shared.observability` | `aws-lambda-powertools[all]` | `logger`, `metrics`, `tracer`, `MetricUnit` |
| `shared.http` | (httpx) | helpers HTTP: `error_response`, `json_response`, `no_content_response`, `resolve_origin`, `verify_turnstile_token`, validators |
| `shared.dynamodb` | `boto3`, `pydantic` (transitivo via shared.aws / shared.core) | ORM tipado: `ContactItem`, `TrackingEventItem`, `CacheItem`, `RateLimitBucketItem`, `RateLimitRuleItem`, `BaseModel`, `GSIMeta`, `TableMeta`, `SchemaDiff` |
| `shared.cache` | `boto3` (transitivo) | `cached` (decorator), `DynamoDBCache`, `CacheEntry`, `CacheStatus` |
| `shared.rate_limit` | (n/a) | `check_or_raise`, `Decision`, `CountryBlockedError`, `IPBlacklistedError`, `RateLimitExceededError` |
| `shared.lambda_kit` | `pydantic`, `httpx` (transitivo) | `BaseController`, `build_event_model`, `run_controller`, `http_handler`, `extract_request`, `import_controller`, `EventModel`, `BaseSettings`, `validate_event` |

## Detalle por subpaquete

### `shared.core`

- **Rol**: primitivos compartidos del dominio. Es la base — ningun otro
  shared depende de el (ni el reverso: shared.core no importa de otros
  subpaquetes).
- **Paquetes externos**: `pydantic[email]>=2.5,<3.0`,
  `pydantic-settings>=2.0,<3.0`. El extra `email` da `email-validator`
  para `EmailStr`.
- **Modulos**: `config.py` (Settings via pydantic-settings),
  `exceptions.py` (jerarquia `ApplicationError`),
  `types.py` (TypedDicts del evento Lambda),
  `ulid.py` (generador UUIDv7).
- **Re-exports**:
  ```python
  from shared.core import (
      BaseModel, ConfigDict, EmailStr, Field, field_validator,
      model_validator,
      Settings, get_settings, settings,
      ApplicationError, ValidationError, RateLimitExceededError,
      IPBlacklistedError, CountryBlockedError, TurnstileError,
      ErrorPayload, JsonResponse, LambdaEvent, RequestContext,
      RequestContextIdentity,
      new_uuidv7,
  )
  ```

### `shared.db`

- **Rol**: schema relacional unificado (PostgreSQL/Neon). Una sola DB,
  35 tablas (CV + datos del visitante).
- **Paquetes externos**: `sqlalchemy>=2.0,<3.0`, `alembic>=1.13,<2.0`,
  `psycopg[binary]>=3.2,<4.0`.
- **internal-deps**: `aws` (para SSM url resolver).
- **Re-exports**:
  ```python
  from shared.db import (
      # SQLAlchemy:
      select, func, pg_insert, Session,
      # ORM del dominio:
      Base, TimestampMixin, UUIDPKMixin, db_session, get_engine,
      # Repository:
      RepositoryError, insert_contact, insert_tracking,
      is_event_processed, list_tables, mark_event_processed,
      # Alembic runner (lo usa la Lambda db):
      build_config, current_revision, run_current, run_downgrade,
      run_migrate, run_show_migrations, run_stamp,
  )
  ```

### `shared.aws`

- **Rol**: clientes boto3 de los servicios AWS. Singletons module-scope
  (DynamoDB Resource, SES client). SSM con cache Powertools.
- **Paquetes externos**: `boto3>=1.34.0,<2.0`,
  `aws-lambda-powertools[all]>=3.0.0,<4.0`.
- **Modulos**: `dynamodb.py` (resource lazy + get_table),
  `dynamodb_types.py` (re-export de boto3.dynamodb.types),
  `ses.py` (sesv2 client + helper send_email),
  `ssm.py` (Parameter Store + Secrets).
- **Re-exports**:
  ```python
  from shared.aws import (
      get_resource, get_table, reset_resource_cache,
      ses, send_email,
      TypeDeserializer, TypeSerializer,
      get_parameter, get_secret, clear_cache,
  )
  ```

### `shared.observability`

- **Rol**: logging + tracing + metrics de Powertools v3. Instancias
  module-scope. Re-exporta `MetricUnit` para que los services no
  importen Powertools directo.
- **Paquetes externos**: `aws-lambda-powertools[all]>=3.0.0,<4.0`.
- **Re-exports**:
  ```python
  from shared.observability import logger, metrics, tracer, MetricUnit
  ```

### `shared.http`

- **Rol**: helpers HTTP genericos (responses, CORS, IP/country
  extraction, Turnstile validation, sanitizers).
- **Paquetes externos**: `httpx` (para Turnstile).
- **Re-exports**: `cors_headers`, `is_allowed_origin`,
  `public_cors_origin`, `resolve_origin`, `extract_country`,
  `extract_ip`, `error_response`, `json_response`,
  `no_content_response`, `verify_turnstile_token`,
  `is_valid_country`, `is_valid_email`, `sanitize_text`.

### `shared.dynamodb`

- **Rol**: ORM tipado sobre DynamoDB. Cada tabla tiene su `Item` con
  validacion pydantic + save() / get() / ...
- **Paquetes externos**: indirectos (pydantic via shared.core, boto3
  via shared.aws).
- **Re-exports**: `ContactItem`, `TrackingEventItem`, `CacheItem`,
  `RateLimitBucketItem`, `RateLimitRuleItem`, `BaseModel`, `GSIMeta`,
  `TableMeta`, `SchemaDiff`.

### `shared.cache`

- **Rol**: cache TTL sobre DynamoDB con stampede prevention,
  stale-while-revalidate, tag invalidation. Vive en
  `serverless/lambda/shared/cache/`.
- **Re-exports**: `cached` (decorator), `DynamoDBCache`, `CacheEntry`,
  `CacheStatus`.

### `shared.rate_limit`

- **Rol**: rate-limiting per-IP con DynamoDB (alternativa a WAF).
  Sliding window weighted, auto-blacklist, country rules.
- **Re-exports**: `check_or_raise`, `Decision`, errores especificos.

### `shared.lambda_kit`

- **Rol**: el "kit" del estandar lambda-controller. Provee
  `BaseController`, el dispatcher, el http_handler generico, la
  validacion de eventos, el import_controller dinamico, el ErrorCode
  enum, etc.
- **internal-deps**: `core`, `http`, `observability`.
- **Re-exports**: `BaseController`, `set_app_config`, `BaseSettings`,
  `DispatchResult`, `run_controller`, `ErrorCode`, `build_event_model`,
  `ExtractedRequest`, `extract_request`, `http_handler`,
  `import_controller`, `resolve_operation`, `LogMetricType`,
  `validate_event`.

## Relaciones (internal-deps)

```text
shared.core            -> []
shared.aws             -> []
shared.observability   -> []
shared.http            -> [core]
shared.db              -> [aws]
shared.dynamodb        -> [core, aws]
shared.cache           -> [aws, core]
shared.rate_limit      -> [core, dynamodb]
shared.lambda_kit      -> [core, http, observability]
```

devtools (`shared_resolver.py`) lee estos `internal-deps` para
calcular el cierre transitivo de cada Lambda al armar el zip de
deploy: solo se vendoriza el cierre real (no todos los subpaquetes).

## Como agregar un re-export nuevo

1. Editar el `__init__.py` del subpaquete portador: agregar el `from
   <paquete> import <simbolo>` y a `__all__`.
2. Test unit en
   `serverless/lambda/shared/tests/unit/shared/<X>/test_<paquete>_reexport.py`.
3. Actualizar este documento (tabla resumen + detalle del subpaquete).
4. `serverless lint-deps` debe pasar.

## Navegacion

- [Volver al README](README.md)
- [Procedimientos de migracion](02-migracion-y-extension.md)
- Regla autoritativa: `.claude/rules/lambda-shared-imports.md`
