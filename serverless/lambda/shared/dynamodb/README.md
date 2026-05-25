# ORM DynamoDB — `shared/dynamodb/`

> ORM minimalista para las 5 tablas DynamoDB del backend serverless del
> portfolio. Un `BaseModel` Pydantic encapsula todo el acceso boto3,
> convierte `Decimal` de forma transparente y centraliza el patron
> antes disperso (`boto3.resource` inline, loops de campos opcionales,
> conversion `Decimal` triplicada).

## Tabla de contenidos

| Tema | Cuando leer |
|------|-------------|
| Reglas criticas | Antes de tocar cualquier cosa de este modulo |
| Estructura | Para ubicar un archivo |
| El `BaseModel` | Antes de crear/usar un modelo |
| Modelos por tabla | Para saber que tabla mapea a que modelo |
| DML vs DDL | Para entender que puede y que NO puede el ORM |
| Por que `infra.yaml` sigue siendo el dueno del DDL | Antes de proponer "que el ORM cree las tablas" |
| Uso | Ejemplos de CRUD, atomicas, query, verificacion |

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** el acceso a las 5 tablas pasa por un modelo del ORM
  (`ContactItem`, `TrackingEventItem`, `CacheItem`,
  `RateLimitBucketItem`, `RateLimitRuleItem`). NUNCA `boto3.resource('dynamodb')`
  directo en codigo de dominio.
- **SIEMPRE** las tablas reales de dev/stage/prod las crea
  `serverless/infra/infra.yaml` (CloudFormation). `create_table` /
  `ensure_table` del ORM son SOLO para tests (moto) y entorno local.
- **SIEMPRE** que se cambie el `KeySchema` / TTL / GSI de una tabla, el
  cambio va en `infra.yaml` **y** en el `TableMeta` del modelo: ambos
  deben coincidir. `check_schema()` lo verifica contra AWS real.
- **NUNCA** el ORM expone `scan` (anti-patron). El unico scan del backend
  vive en `shared/cache/invalidation.py` (tag invalidation, no hay otra
  forma en DynamoDB) y usa el `Table` crudo, no el ORM.
- **NUNCA** el codigo de dominio ve `Decimal`: el `BaseModel` baja
  `Decimal -> int/float` al leer.

## Estructura

```text
shared/dynamodb/
├── __init__.py        # re-exports: BaseModel, TableMeta, GSIMeta, los 5 modelos
├── base.py            # BaseModel: CRUD + query + atomicas + DDL
├── _convert.py        # conversion Decimal <-> Python, filtrado de empty
├── _schema.py         # TableMeta, GSIMeta, SchemaDiff, build_create_table_kwargs
└── models/
    ├── contact.py             # ContactItem
    ├── tracking.py            # TrackingEventItem (incluye GSI)
    ├── cache.py               # CacheItem
    ├── rate_limit_bucket.py   # RateLimitBucketItem
    └── rate_limit_rule.py     # RateLimitRuleItem
```

## El `BaseModel`

Cada tabla es una subclase de `BaseModel` (Pydantic) con un
`Meta: ClassVar[TableMeta]`. El `BaseModel` reusa el resource boto3
singleton de `shared.dynamodb_client` (`get_resource()`): el ORM NO crea
resources propios.

`TableMeta` declara el esquema MINIMO: claves (PK/SK), atributo TTL y
GSIs. NO declara `BillingMode`/`SSE`/`PITR`/`Stream` — eso es exclusivo
de `infra.yaml`.

## Modelos por tabla

| Modelo | Tabla | PK / SK | TTL | GSI |
|--------|-------|---------|-----|-----|
| `ContactItem` | `portfolio-contacts-{stage}` | `id` | — | — |
| `TrackingEventItem` | `portfolio-tracking-{stage}` | `session_id` / `page_id` | `expires_at` | `niche-created_at-index` |
| `CacheItem` | `portfolio-cache-{stage}` | `cache_key` | `expires_at` | — |
| `RateLimitBucketItem` | `portfolio-rate-limit-buckets-{stage}` | `bucket_key` | `expires_at` | — |
| `RateLimitRuleItem` | `portfolio-rate-limit-rules-{stage}` | `rule_key` / `kind` | `expires_at` | — |

## DML vs DDL

El ORM expone dos capas:

- **DML (datos)** — uso normal en runtime:
  `save`, `get`, `query`, `update`, `delete`, y las atomicas
  `increment` (`ADD`), `put_if_absent` y `conditional_update`
  (`ConditionExpression`).
- **DDL (esquema)** — verificacion + creacion:
  `table_exists`, `describe_table`, `check_schema` (drift detection
  contra AWS real). `create_table` / `ensure_table` SOLO para
  tests/local.

## Por que `infra.yaml` sigue siendo el dueno del DDL

El ORM **no crea las tablas de dev/stage/prod**. La razon no es estetica:

- `infra.yaml` exporta `ContactsStreamArn` / `TrackingStreamArn`. El
  stack del `stream_processor` los consume via `Fn::ImportValue` para
  conectar el DynamoDB Stream -> Lambda. Solo CloudFormation puede
  conectar ese stream de forma declarativa e idempotente.
- `infra.yaml` exporta los `*TableArn`, que los 4 Lambdas usan para su
  IAM least-privilege.
- `PITR`, `SSE`, `BillingMode`, `StreamSpecification` los gestiona
  CloudFormation declarativamente.

El ORM y los DynamoDB Streams son capas distintas:

```text
contact_form / tracking_pixel  --escribe-->  DynamoDB
        (el ORM)                                |
                              DynamoDB Stream (evento auto de AWS)
                                                 |
                                    stream_processor  --escribe-->  Neon
```

El ORM es la capa de escritura/lectura. El Stream replica a Neon. El ORM
no puede sustituir al Stream.

## Uso

```python
from shared.dynamodb import ContactItem, RateLimitBucketItem, TrackingEventItem

# Escribir (to_item omite los campos None/'' automaticamente)
ContactItem(
    id='01HZ...', created_at='2026-05-21T10:00:00+00:00',
    name='Pablo', email='pablo@example.com', message='Hola',
).save()

# Leer
contact = ContactItem.get('01HZ...')              # PK simple
event = TrackingEventItem.get('sess-1', 'page-1') # PK + SK

# Incremento atomico (ADD) + SET en el mismo update
RateLimitBucketItem.increment(
    'ip#1.2.3.4#endpoint#/contact#window#100',
    set_fields={'expires_at': 1715000200},
    count=1, turnstile_tokens=1,
)

# Escritura condicional (lock distribuido)
written = CacheItem(cache_key='lock:job', value='holder', ...).put_if_absent()

# Query por GSI
events = TrackingEventItem.query('fintech', index_name='niche-created_at-index')

# Verificacion de esquema (drift contra AWS real, necesita credenciales)
diff = TrackingEventItem.check_schema()
assert diff.in_sync
```

## Navegacion

- Capa de bajo nivel: `shared/dynamodb_client.py` (resource singleton)
- Stack de infra (dueno del DDL): `serverless/infra/infra.yaml`
- Skills relacionadas: `aws-dynamodb`, `dynamodb-cache`,
  `serverless-rate-limit`
- Rule: `.claude/rules/lambda-controller.md`
