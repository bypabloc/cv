# 01 — Arquitectura: recursos compartidos + Lambdas

> [<- README](README.md) | [Siguiente: 02-flujos ->](02-flujos.md)

El backend NO usa SAM ni CloudFormation. devtools provisiona cada
recurso AWS de forma imperativa con AWS CLI y registra lo creado en un
archivo de estado local. Hay dos planos: los recursos compartidos
(tablas DynamoDB, API Gateway, DLQ SQS) y los 4 Lambdas. Cada plano se
provisiona por separado.

## 1. Los recursos

### Recursos compartidos (`resources/`)

| Recurso | Tipo | Contenido |
|---------|------|-----------|
| `portfolio-contacts-<stage>` | DynamoDB | tabla `contacts` (con Stream) |
| `portfolio-tracking-<stage>` | DynamoDB | tabla `tracking` (con Stream + TTL) |
| `portfolio-cache-<stage>` | DynamoDB | tabla `cache` |
| `portfolio-rate-limit-rules-<stage>` | DynamoDB | tabla `rate-limit-rules` |
| `portfolio-rate-limit-buckets-<stage>` | DynamoDB | tabla `rate-limit-buckets` |
| `portfolio-api-<stage>` | API Gateway | API REST REGIONAL (sin metodos) |
| `portfolio-stream-processor-dlq-<stage>` | SQS | DLQ del `stream_processor` |

### Lambdas (`services/`)

| Lambda | Trigger | Contenido |
|--------|---------|-----------|
| `portfolio-db-<stage>` | invoke directo | Lambda `db` — gestion del schema Alembic (sin API) |
| `portfolio-contact-form-<stage>` | `http` | Lambda `contact_form` + ruta `POST /contact` sobre la API compartida |
| `portfolio-tracking-pixel-<stage>` | `http` | Lambda `tracking_pixel` + ruta `POST /track` sobre la API compartida |
| `portfolio-stream-processor-<stage>` | `on-table-changes` | Lambda `stream_processor` + Event Source Mappings de los Streams de `contacts` y `tracking` |

`<stage>` es `dev`, `stage` o `prod`. Cada stage es un set completo de
todos los recursos, aislado, con su propio set de archivos de estado.

## 2. Por que recurso-por-recurso y no un stack de infra unico

| Aspecto | IaC declarativa monolitica | Provisioning por recurso (actual) |
|---------|----------------------------|-----------------------------------|
| Deploy de 1 recurso | Redeploya todo el stack | Solo ese recurso — rapido, blast radius minimo |
| Falla en un deploy | Rollback de TODO | Aislada al recurso que fallo |
| Recrear/borrar un recurso | Bloqueado si su identificador esta en uso | Libre: los Lambdas leen SSM, sin lock |
| Acoplamiento | Referencias cruzadas rigidas entre stacks | Lectura de SSM, sin dependencias rigidas |
| Ownership | Difuso | Cada recurso/Lambda es duena de su estado |

El modelo declarativo monolitico impide gestionar cada recurso por
separado y agrega una capa opaca de traduccion. La solucion: provisionar
cada recurso por separado con AWS CLI + SSM Parameter Store para que los
Lambdas resuelvan los identificadores sin acoplarse.

## 3. Los recursos compartidos (`resources/<tipo>/<nombre>.yaml`)

Cada archivo `serverless/lambda/resources/<tipo>/<nombre>.yaml` es un
descriptor en un **esquema propio de devtools** — plano, sin funciones
intrinsecas — que declara que recurso crear: tipo, nombre, atributos y
que paths SSM publicar. `infra_provision.py` lee el descriptor y emite
las llamadas AWS CLI (`aws dynamodb create-table`, `aws apigateway
create-rest-api`, `aws sqs create-queue`, `aws ssm put-parameter`).

Ejemplo `resources/dynamodb/contacts.yaml`:

```yaml
# Esquema devtools — descriptor plano, sin IaC declarativa.
kind: dynamodb-table
name: portfolio-contacts-${stage}
billing_mode: PAY_PER_REQUEST
hash_key: { name: id, type: S }
stream: NEW_AND_OLD_IMAGES
point_in_time_recovery: true
encryption: true
publishes_ssm:                    # devtools escribe estos SSM tras crear
  name: /portfolio/${stage}/dynamodb/contacts/name
  arn: /portfolio/${stage}/dynamodb/contacts/arn
  stream_arn: /portfolio/${stage}/dynamodb/contacts/stream-arn
tags: { Project: portfolio, ManagedBy: devtools }
```

`resources/_header.yaml` quedo como documentacion del patron.

### Publicacion a SSM

Tras crear cada recurso, devtools publica sus identificadores como SSM
Parameters (`String` planos). Convencion del `Name`:

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
| `/portfolio/{stage}/dynamodb/contacts/name` | recurso `contacts` | `contact_form`, `stream_processor` |
| `/portfolio/{stage}/dynamodb/contacts/arn` | recurso `contacts` | politicas IAM de los Lambdas |
| `/portfolio/{stage}/dynamodb/contacts/stream-arn` | recurso `contacts` | `stream_processor` (Event Source Mapping) |
| `/portfolio/{stage}/dynamodb/tracking/{name,arn,stream-arn}` | recurso `tracking` | `tracking_pixel`, `stream_processor` |
| `/portfolio/{stage}/dynamodb/cache/{name,arn}` | recurso `cache` | `contact_form`, `tracking_pixel` |
| `/portfolio/{stage}/dynamodb/rate-limit-rules/{name,arn}` | recurso `rate-limit-rules` | `contact_form`, `tracking_pixel` |
| `/portfolio/{stage}/dynamodb/rate-limit-buckets/{name,arn}` | recurso `rate-limit-buckets` | `contact_form`, `tracking_pixel` |
| `/portfolio/{stage}/api_gateway/portfolio-api/{id,root-resource-id,access-log-group-arn}` | recurso `portfolio-api` | `contact_form`, `tracking_pixel` |
| `/portfolio/{stage}/sqs/stream-processor-dlq/{arn,url}` | recurso `stream-processor-dlq` | `stream_processor` |

Estos paths son `String` planos (un nombre/ARN de recurso no es secreto).

## 4. Como los Lambdas consumen los recursos

Hay dos vias, segun el momento en que se necesita el valor:

- **Runtime (cold start)**: el Lambda lee el **nombre de la tabla**
  DynamoDB con `ssm:GetParameter` en el cold start (module scope).
  devtools le inyecta una env var `SSM_<TABLA>_TABLE_PATH`
  (ej. `SSM_CONTACTS_TABLE_PATH=/portfolio/dev/dynamodb/contacts/name`)
  y el codigo resuelve ese path. Asi un recurso se puede recrear sin
  tocar ni bloquear a los Lambdas.
- **Deploy-time (resolucion en el provisioner)**: el Stream ARN, el DLQ
  ARN y el `ApiId` los resuelve `provisioner.py` con
  `aws ssm get-parameter` al momento del `deploy`. Son necesarios para
  crear el Event Source Mapping y las rutas (`apigateway put-method` /
  `put-integration`) de la API.

```text
recurso  --(aws ssm put-parameter)-->  SSM Parameter Store
                                           |
       cold start (boto3 GetParameter) ----+--> nombre de tabla
       deploy (aws ssm get-parameter) -----+--> ARN/ApiId para el wiring
```

Orden de operacion:

- **Deploy**: recursos compartidos primero (`provision-infra`), luego los
  4 Lambdas (en cualquier orden).
- **Destroy**: el orden es flexible; aun asi conviene borrar los Lambdas
  antes que los recursos para no dejar Event Source Mappings apuntando a
  tablas inexistentes. `serverless destroy` ya borra en orden inverso al
  de creacion.

## 5. Estructura de carpetas

```text
serverless/
└── lambda/
    ├── .state/                     # estado local de devtools (gitignored)
    │   └── <scope>-<stage>.json     # un archivo por recurso/lambda x stage
    ├── resources/                  # un descriptor devtools por recurso
    │   ├── _header.yaml             # documentacion del patron (no se provisiona)
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
├── manifest.yaml                # MANIFIESTO: fuente de verdad de la config
├── pyproject.toml               # deps del Lambda (PEP 621) — uv las gestiona
├── build/                       # EFIMERO: artefacto de deploy (en .gitignore)
├── build.zip                    # EFIMERO: zip que se sube a AWS (.gitignore)
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
dependencias de deploy cruzadas entre Lambdas.

## 7. Los 4 Lambdas

| Lambda | Trigger | Memoria | Timeout |
|--------|---------|---------|---------|
| `db` | `direct` (invoke directo) | 512 MB | 120s |
| `contact_form` | `http` `POST /contact` | 512 MB | 30s |
| `tracking_pixel` | `http` `POST /track` | 256 MB | 10s |
| `stream_processor` | `on-table-changes` (`contacts`, `tracking`) | 512 MB | 60s |

### El manifiesto `manifest.yaml` (formato dev)

`manifest.yaml` describe el Lambda en terminos de DESARROLLADOR: sin
ARNs, sin politicas IAM. `provisioner.py` lo lee directamente y lo
traduce a llamadas AWS CLI.

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

`provisioner.py` lo traduce a llamadas AWS CLI:

- `trigger: http` -> `aws apigateway put-method` + `put-integration` +
  `create-deployment` sobre la API compartida; el `ApiId` lo resuelve el
  provisioner con `aws ssm get-parameter`.
- `trigger: on-table-changes` -> `aws lambda create-event-source-mapping`
  por cada Stream (Stream ARN resuelto via SSM) + DLQ en `OnFailure`.
- `uses.tables` -> politica IAM (`aws iam put-role-policy`) scoped al ARN
  de cada tabla + env var `SSM_<TABLA>_TABLE_PATH` para que el Lambda
  resuelva el nombre en runtime.
- `uses.secrets` -> `ssm:GetParameter` del path completo + `kms:Decrypt`.
- `uses.sends-email` -> `ses:SendEmail` con condition de remitente.

devtools arma el `build.zip` (artefacto con uv + vendoring selectivo) y
lo sube con `aws lambda create-function` / `update-function-code`. El
`manifest.yaml` es la unica fuente de verdad de la config: para cambiar
algo se edita y se re-deploya. devtools registra lo creado en el archivo
de estado (ver [05-estado-local.md](05-estado-local.md)).

## 8. Stages

| Stage | Descripcion |
|-------|-------------|
| `local` | Lambda corre en local (RIE via Docker o modo directo) con eventos de `events/` — sin AWS |
| `dev` | Todos los recursos provisionados en `us-east-1` (cuenta dev) |
| `stage` | Todos los recursos provisionados (pre-produccion) |
| `prod` | Todos los recursos provisionados (cuenta productiva) |

## 9. Region y costos

- **Region**: `us-east-1` (misma que SES production access y Neon).
- **Runtime**: Python 3.13, arm64 Graviton2.
- **Costo**: ~$0/mes — todo dentro del free tier perpetuo. Sin AWS WAF
  (rate-limit self-managed con DynamoDB), sin CloudWatch Alarms
  operacionales (solo el AWS Billing Alarm global gratis), retention de
  logs 7 dias.

---

[<- README](README.md) | [Siguiente: 02-flujos ->](02-flujos.md)
