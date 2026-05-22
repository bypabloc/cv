# 01 — Arquitectura: stacks de recurso + stacks de Lambda

> [<- README](README.md) | [Siguiente: 02-flujos ->](02-flujos.md)

El backend NO es un stack SAM monolitico, ni tiene un unico stack de
infra. Son N stacks CloudFormation independientes: un stack por cada
recurso compartido (tabla DynamoDB, API Gateway, DLQ SQS) y un stack por
cada Lambda. Cada uno se deploya por separado.

## 1. Los stacks

### Stacks de recurso (`resources/`)

| Stack | Tipo | Contenido |
|-------|------|-----------|
| `portfolio-dynamodb-contacts-<stage>` | Recurso | tabla DynamoDB `contacts` (con Stream) |
| `portfolio-dynamodb-tracking-<stage>` | Recurso | tabla DynamoDB `tracking` (con Stream + TTL) |
| `portfolio-dynamodb-cache-<stage>` | Recurso | tabla DynamoDB `cache` |
| `portfolio-dynamodb-rate-limit-rules-<stage>` | Recurso | tabla DynamoDB `rate-limit-rules` |
| `portfolio-dynamodb-rate-limit-buckets-<stage>` | Recurso | tabla DynamoDB `rate-limit-buckets` |
| `portfolio-api_gateway-portfolio-api-<stage>` | Recurso | API Gateway REST REGIONAL (sin metodos) |
| `portfolio-sqs-stream-processor-dlq-<stage>` | Recurso | DLQ SQS del `stream_processor` |

### Stacks de Lambda (`services/`)

| Stack | Tipo | Contenido |
|-------|------|-----------|
| `portfolio-db-<stage>` | Lambda | Lambda `db` — gestion del schema Alembic (invoke directo, sin API) |
| `portfolio-contact-form-<stage>` | Lambda | Lambda `contact_form` + ruta `POST /contact` sobre la API compartida |
| `portfolio-tracking-pixel-<stage>` | Lambda | Lambda `tracking_pixel` + ruta `POST /track` sobre la API compartida |
| `portfolio-stream-processor-<stage>` | Lambda | Lambda `stream_processor` + Event Source Mappings de los Streams de `contacts` y `tracking` |

`<stage>` es `dev`, `stage` o `prod`. Cada stage es un set completo de
todos los stacks, aislado.

## 2. Por que stack-por-recurso y no 1 stack de infra

| Aspecto | Stack de infra unico | Stack-por-recurso (actual) |
|---------|----------------------|----------------------------|
| Deploy de 1 recurso | Redeploya todo el stack | Solo su stack — rapido, blast radius minimo |
| Falla en un deploy | Rollback de TODO | Aislada al stack que fallo |
| Recrear/borrar un recurso | Bloqueado: su `Export` esta en uso | Libre: no hay `Export`, los Lambdas leen SSM |
| Acoplamiento | `Fn::ImportValue` crea dependencias rigidas | Lectura de SSM en runtime, sin lock |
| Ownership | Difuso | Cada recurso/Lambda es duena de su stack |

CloudFormation prohibe borrar o recrear un stack cuyo `Export` esta en
uso por otro stack. El modelo de infra unica + `Fn::ImportValue` impedia
gestionar cada recurso por separado. La solucion: un stack por recurso +
SSM Parameter Store en lugar de `Export`.

## 3. Los stacks de recurso (`resources/<tipo>/<nombre>.yaml`)

Cada archivo `serverless/lambda/resources/<tipo>/<nombre>.yaml` es un
template CloudFormation COMPLETO y autonomo: trae su
`AWSTemplateFormatVersion`, `Description`, `Parameters` (el `Stage`),
`Resources` y `Outputs`. El nombre del stack resultante es
`portfolio-<tipo>-<nombre>-<stage>`.

`resources/_header.yaml` ya NO se ensambla con nada: quedo como
documentacion del patron.

### Publicacion a SSM (en vez de `Export`)

Cada stack de recurso publica sus identificadores como recursos
`AWS::SSM::Parameter`, NO como `Outputs` con `Export`. Convencion del
`Name`:

```text
/portfolio/{stage}/{tipo}/{nombre}/{atributo}

  {stage}     dev | stage | prod
  {tipo}      carpeta del recurso: dynamodb | api_gateway | sqs
  {nombre}    archivo sin extension: contacts, portfolio-api, ...
  {atributo}  kebab-case: arn, name, stream-arn, id, url, ...
```

Ejemplos:

| Path SSM | Lo publica | Lo consume |
|----------|------------|------------|
| `/portfolio/{stage}/dynamodb/contacts/name` | stack `contacts` | `contact_form`, `stream_processor` |
| `/portfolio/{stage}/dynamodb/contacts/arn` | stack `contacts` | politicas IAM de los Lambdas |
| `/portfolio/{stage}/dynamodb/contacts/stream-arn` | stack `contacts` | `stream_processor` (Event Source Mapping) |
| `/portfolio/{stage}/dynamodb/tracking/{name,arn,stream-arn}` | stack `tracking` | `tracking_pixel`, `stream_processor` |
| `/portfolio/{stage}/dynamodb/cache/{name,arn}` | stack `cache` | `contact_form`, `tracking_pixel` |
| `/portfolio/{stage}/dynamodb/rate-limit-rules/{name,arn}` | stack `rate-limit-rules` | `contact_form`, `tracking_pixel` |
| `/portfolio/{stage}/dynamodb/rate-limit-buckets/{name,arn}` | stack `rate-limit-buckets` | `contact_form`, `tracking_pixel` |
| `/portfolio/{stage}/api_gateway/portfolio-api/{id,root-resource-id,access-log-group-arn}` | stack `portfolio-api` | `contact_form`, `tracking_pixel` |
| `/portfolio/{stage}/sqs/stream-processor-dlq/{arn,url}` | stack `stream-processor-dlq` | `stream_processor` |

Estos paths son `String` planos (un nombre/ARN de recurso no es secreto).

## 4. Como los Lambdas consumen los recursos

Hay dos vias, segun el momento en que se necesita el valor:

- **Runtime (cold start)**: el Lambda lee el **nombre de la tabla**
  DynamoDB con `ssm:GetParameter` en el cold start (module scope). El
  template SAM le inyecta una env var `SSM_<TABLA>_TABLE_PATH`
  (ej. `SSM_CONTACTS_TABLE_PATH=/portfolio/dev/dynamodb/contacts/name`)
  y el codigo resuelve ese path. Asi un stack de recurso se puede
  redeployar sin tocar ni bloquear los stacks de los Lambdas.
- **Deploy-time (dynamic reference)**: el Stream ARN, el DLQ ARN y el
  `ApiId` se resuelven con dynamic references CloudFormation
  (`{{resolve:ssm:...}}`) en el `template.yaml` SAM generado. Son
  necesarios para crear el Event Source Mapping y los `Method`/`Resource`
  de la API.

```text
stack de recurso  --(AWS::SSM::Parameter)-->  SSM Parameter Store
                                                  |
            cold start (boto3 GetParameter) ------+--> nombre de tabla
            deploy ({{resolve:ssm:...}})  --------+--> ARN/ApiId en el SAM
```

Orden de operacion:

- **Deploy**: stacks de recurso primero (`deploy-infra`), luego los 4
  Lambdas (en cualquier orden).
- **Delete**: no hay `Export` en uso, asi que el orden es flexible; aun
  asi conviene borrar los Lambdas antes que los recursos para no dejar
  Event Source Mappings apuntando a tablas inexistentes.

## 5. Estructura de carpetas

```text
serverless/
└── lambda/
    ├── resources/                  # un stack CloudFormation por recurso
    │   ├── _header.yaml             # documentacion del patron (no se deploya)
    │   ├── dynamodb/
    │   │   ├── contacts.yaml
    │   │   ├── tracking.yaml
    │   │   ├── cache.yaml
    │   │   ├── rate-limit-rules.yaml
    │   │   └── rate-limit-buckets.yaml
    │   ├── api_gateway/
    │   │   └── portfolio-api.yaml
    │   └── sqs/
    │       └── stream-processor-dlq.yaml
    │
    ├── pyproject.toml               # uv workspace (raiz) — agrupa shared/ + services/
    ├── uv.lock                      # lockfile unico del workspace
    │
    ├── shared/                      # libreria comun (codigo fuente, versionado)
    │   │                            # 8 subpaquetes por dominio, cada uno con
    │   │                            # su pyproject.toml (deps externas + internal-deps)
    │   ├── core/                    # config, exceptions, types, ulid
    │   ├── aws/                     # dynamodb, ses, ssm (clientes AWS)
    │   ├── observability/           # logger, tracer, metrics
    │   ├── http/                    # cors, responses, ip_extractor, turnstile, validators
    │   ├── dynamodb/                # acceso DynamoDB de dominio
    │   ├── cache/                   # cache con DynamoDB TTL
    │   ├── rate_limit/              # rate-limit per-IP
    │   ├── db/                      # ORM SQLAlchemy + Alembic (schema unificado)
    │   └── tests/                   # tests de la libreria comun shared/
    │
    └── services/                    # un directorio por Lambda
        ├── db/                      # Lambda db
        ├── contact_form/            # Lambda contact_form
        ├── tracking_pixel/          # Lambda tracking_pixel
        └── stream_processor/        # Lambda stream_processor
```

`serverless/lambda/` es un **uv workspace**: el `pyproject.toml` de la
raiz agrupa `shared/` (sus 8 subpaquetes) y los 4 Lambdas de `services/`,
con un `uv.lock` unico. Cada Lambda y cada subpaquete de `shared/` tiene
su propio `pyproject.toml` (PEP 621) declarando sus dependencias —
externas e `internal-deps` (otros subpaquetes de `shared/`). devtools
gestiona las deps con uv; no hay `requirements.txt`.

Cada Lambda de `services/` sigue el formato `lambda-controller`:

```text
services/<lambda>/
├── lambda.yaml                  # MANIFIESTO: fuente de verdad de la config
├── template.yaml                # SAM generado (EFIMERO, en .gitignore)
├── pyproject.toml               # deps del Lambda (PEP 621) — uv las gestiona
├── build/                       # EFIMERO: artefacto de deploy (en .gitignore)
├── events/                      # eventos de ejemplo para `run`
├── core/
│   ├── handler.py               # ENTRYPOINT — router delgado
│   ├── controllers/<operation>/ # orquestadores por operation
│   ├── services/                # logica de negocio
│   ├── models/                  # validacion Pydantic del payload
│   ├── settings/                # AppConfig + OPERATIONS
│   └── utils/                   # BaseController, invoker, ...
└── tests/{unit,integration}/
```

El vendor de `shared/` NO vive en `core/shared/`: devtools lo coloca en
`build/core/shared/` al armar el artefacto de deploy (ver seccion 6).

Detalle completo del formato: [.claude/rules/lambda-controller.md](../../rules/lambda-controller.md)
y [.claude/docs/lambda-controller/](../lambda-controller/).

## 6. La libreria comun vendorizada (selectiva)

El codigo compartido entre Lambdas vive en `serverless/lambda/shared/`,
organizado en 8 subpaquetes por dominio (`core`, `aws`, `observability`,
`http`, `dynamodb`, `cache`, `rate_limit`, `db`). NO se publica como
Lambda Layer.

Para armar el artefacto de deploy, devtools arma el directorio `build/`
del Lambda:

1. Instala las dependencias del Lambda con uv
   (`uv pip install --target build/`), resueltas desde el `uv.lock` del
   workspace.
2. **Vendoriza SELECTIVAMENTE** solo los subpaquetes de `shared/` que el
   Lambda realmente usa. devtools calcula el cierre transitivo de
   dependencias por **AST scan** de los imports `from shared.<sub>...` y
   copia esos subpaquetes (y los que ellos importan a su vez) a
   `build/core/shared/`.

```text
serverless/lambda/shared/<sub>   --(AST scan: cierre transitivo)-->
   (fuente, versionado)              build/core/shared/<sub>
                                     (efimero, .gitignore)
```

Los imports en el codigo del Lambda son explicitos al subpaquete
(`from shared.observability.logger import logger`,
`from shared.aws.dynamodb import get_table`,
`from shared.core.exceptions import X`) y resuelven contra el vendor.
`shared/__init__.py` ya no re-exporta nada — siempre se importa la ruta
completa del subpaquete.

`build/` es efimero (`.gitignore`); se regenera en cada `deploy` o `run`.
Asi cada Lambda empaqueta solo el codigo comun que importa, sin Layers ni
dependencias de deploy cruzadas entre stacks.

## 7. Los 4 Lambdas

| Lambda | Trigger | Memoria | Timeout | Stack |
|--------|---------|---------|---------|-------|
| `db` | `direct` (invoke directo) | 512 MB | 120s | `portfolio-db-<stage>` |
| `contact_form` | `http` `POST /contact` | 512 MB | 30s | `portfolio-contact-form-<stage>` |
| `tracking_pixel` | `http` `POST /track` | 256 MB | 10s | `portfolio-tracking-pixel-<stage>` |
| `stream_processor` | `on-table-changes` (`contacts`, `tracking`) | 512 MB | 60s | `portfolio-stream-processor-<stage>` |

### El manifiesto `lambda.yaml` (formato dev)

`lambda.yaml` describe el Lambda en terminos de DESARROLLADOR: sin ARNs,
sin politicas IAM. devtools lo traduce al SAM.

Campos:

| Campo | Que describe |
|-------|--------------|
| `name`, `description` | Identidad |
| `runtime`, `handler`, `memory`, `timeout` | Runtime |
| `trigger` | Como se invoca: `direct` \| `http` (con `method`+`path`) \| `on-table-changes` (con `tables`) |
| `uses.tables` | Tablas DynamoDB con nivel de acceso (`read` \| `write` \| `read-write`) |
| `uses.secrets` | Secretos SSM por nombre corto (`turnstile-secret`, `neon-url`, ...) |
| `uses.sends-email` | `true` si el Lambda manda email por SES |
| `env` | Variables de entorno por stage (`default` + override por `dev`/`stage`/`prod`) |

devtools (`devtools/serverless/sam_generate.py`) lo traduce:

- `trigger: http` -> `AWS::ApiGateway::Method` + `Resource` sobre la API
  compartida; el `ApiId` se resuelve con `{{resolve:ssm:...}}`.
- `trigger: on-table-changes` -> Event Source Mapping por cada Stream
  (Stream ARN resuelto con `{{resolve:ssm:...}}`) + DLQ en `OnFailure`.
- `uses.tables` -> politica IAM scoped al ARN de cada tabla + env var
  `SSM_<TABLA>_TABLE_PATH` para que el Lambda resuelva el nombre en
  runtime.
- `uses.secrets` -> `ssm:GetParameter` del path completo + `kms:Decrypt`.
- `uses.sends-email` -> `ses:SendEmail` con condition de remitente.

El `template.yaml` resultante apunta `CodeUri` al directorio `build/`
(el artefacto ya armado por devtools con uv + vendoring selectivo) y NO
lleva `Metadata.BuildMethod`: `sam deploy` solo sube ese artefacto, no
corre `pip` ni `sam build`. El `template.yaml` es EFIMERO: nunca se
edita ni commitea. Si hay que cambiar la config se edita el `lambda.yaml`
y se regenera con `sam-generate`.

## 8. Stages

| Stage | Descripcion |
|-------|-------------|
| `local` | `sam local invoke` con eventos de `events/` — sin AWS |
| `dev` | Todos los stacks desplegados en `us-east-1` (cuenta dev) |
| `stage` | Todos los stacks desplegados (pre-produccion) |
| `prod` | Todos los stacks desplegados (cuenta productiva) |

## 9. Region y costos

- **Region**: `us-east-1` (misma que SES production access y Neon).
- **Runtime**: Python 3.13, arm64 Graviton2.
- **Costo**: ~$0/mes — todo dentro del free tier perpetuo. Sin AWS WAF
  (rate-limit self-managed con DynamoDB), sin CloudWatch Alarms
  operacionales (solo el AWS Billing Alarm global gratis), retention de
  logs 7 dias.

---

[<- README](README.md) | [Siguiente: 02-flujos ->](02-flujos.md)
