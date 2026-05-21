# 01 — Arquitectura de 5 stacks

> [<- README](README.md) | [Siguiente: 02-flujos ->](02-flujos.md)

El backend NO es un stack SAM monolitico. Son 5 stacks CloudFormation
independientes, cada uno desplegable por separado.

## 1. Los 5 stacks

| Stack | Tipo | Contenido |
|-------|------|-----------|
| `portfolio-infra-<stage>` | Infra compartida | API Gateway REST (sin metodos) + 5 tablas DynamoDB + DLQ SQS |
| `portfolio-db-<stage>` | Lambda | Lambda `db` — gestion del schema Alembic (invoke directo, sin API) |
| `portfolio-contact-form-<stage>` | Lambda | Lambda `contact_form` + ruta `POST /contact` sobre la API compartida |
| `portfolio-tracking-pixel-<stage>` | Lambda | Lambda `tracking_pixel` + ruta `POST /track` sobre la API compartida |
| `portfolio-stream-processor-<stage>` | Lambda | Lambda `stream_processor` + Event Source Mappings de los Streams de `contacts` y `tracking` |

`<stage>` es `dev`, `stage` o `prod`. Cada stage es un set completo de
los 5 stacks, aislado.

## 2. Por que 5 stacks y no 1

| Aspecto | Stack monolitico | 5 stacks (actual) |
|---------|------------------|-------------------|
| Deploy de 1 Lambda | Redeploya todo el stack | Solo su stack — rapido, blast radius minimo |
| Falla en un deploy | Rollback de TODO | Aislada al stack que fallo |
| Recursos compartidos | Mezclados con la logica | Aislados en el stack de infra |
| Tablas DynamoDB | Borrado accidental con el stack | En el stack de infra, ciclo de vida propio |
| Ownership | Difuso | Cada Lambda es duena de su stack |

## 3. El stack de infra (`portfolio-infra-<stage>`)

Template versionado: `serverless/infra/infra.yaml`. Es la base que los
4 stacks de Lambda consumen. Contiene:

- **`AWS::ApiGateway::RestApi`** (`portfolio-api-<stage>`) — REST API
  REGIONAL **sin metodos**. Los metodos `/contact` y `/track` los agregan
  los stacks de `contact_form` y `tracking_pixel`. CloudFormation permite
  una REST API sin metodos.
- **5 tablas DynamoDB** (`PAY_PER_REQUEST`):
  `contacts`, `tracking`, `cache`, `rate-limit-rules`, `rate-limit-buckets`.
- **DLQ SQS** del `stream_processor` (`StreamProcessorDLQ`).
- **`AWS::ApiGateway::Account` + IAM role** para los Access Logs de la API.

Cada recurso publica un Output con `Export` para que los stacks de
Lambda lo importen.

### Exports del stack de infra

El stack de infra exporta (formato `portfolio-infra-<stage>-<Nombre>`):

| Export | Lo consume |
|--------|------------|
| `ApiId`, `ApiRootResourceId` | `contact_form`, `tracking_pixel` (agregan metodos) |
| `ContactsTableName` / `Arn` / `ContactsStreamArn` | `contact_form` (escribe), `stream_processor` (lee el Stream) |
| `TrackingTableName` / `Arn` / `TrackingStreamArn` | `tracking_pixel` (escribe), `stream_processor` (lee el Stream) |
| `CacheTableName` / `Arn` | `contact_form`, `tracking_pixel` (`@cached`) |
| `RateLimitRulesTableName` / `Arn` | `contact_form`, `tracking_pixel` (rate-limit) |
| `RateLimitBucketsTableName` / `Arn` | `contact_form`, `tracking_pixel` (rate-limit) |
| `StreamProcessorDLQArn` / `Name` | `stream_processor` (DLQ en `OnFailure`) |

## 4. Como los Lambdas importan la infra

Cada stack de Lambda referencia los recursos del stack de infra con
`Fn::ImportValue`. devtools genera el `template.yaml` SAM efimero a
partir del `lambda.yaml`, y el `Fn::ImportValue` aparece ahi
automaticamente segun el bloque `uses` del manifiesto.

```text
portfolio-infra-dev          (deploy PRIMERO)
   |  Outputs + Export
   |
   +--> Fn::ImportValue --> portfolio-db-dev
   +--> Fn::ImportValue --> portfolio-contact-form-dev
   +--> Fn::ImportValue --> portfolio-tracking-pixel-dev
   +--> Fn::ImportValue --> portfolio-stream-processor-dev
```

Orden de operacion:

- **Deploy**: infra primero, luego los 4 Lambdas (en cualquier orden).
- **Delete**: los 4 Lambdas primero, infra al final. CloudFormation
  bloquea borrar un `Export` que un stack en uso esta importando.

## 5. Estructura de carpetas

```text
serverless/
├── infra/
│   └── infra.yaml               # template del stack de infra compartida
│
├── shared/                      # libreria comun (codigo fuente, versionado)
│   ├── cors.py  logger.py  ...
│   ├── cache/                   # cache con DynamoDB TTL
│   ├── rate_limit/              # rate-limit per-IP
│   └── db/                      # ORM SQLAlchemy + Alembic (schema unificado)
│
├── src/                         # un directorio por Lambda
│   ├── db/                      # Lambda db
│   ├── contact_form/            # Lambda contact_form
│   ├── tracking_pixel/          # Lambda tracking_pixel
│   └── stream_processor/        # Lambda stream_processor
│
└── tests/                       # tests de la libreria comun shared/
```

Cada Lambda de `src/` sigue el formato `lambda-controller`:

```text
src/<lambda>/
├── lambda.yaml                  # MANIFIESTO: fuente de verdad de la config
├── template.yaml                # SAM generado (EFIMERO, en .gitignore)
├── pytest.ini
├── requirements.txt  requirements-dev.txt
├── events/                      # eventos de ejemplo para run-local
├── core/
│   ├── handler.py               # ENTRYPOINT — router delgado
│   ├── controllers/<operation>/ # orquestadores por operation
│   ├── services/                # logica de negocio
│   ├── models/                  # validacion Pydantic del payload
│   ├── settings/                # AppConfig + OPERATIONS
│   ├── utils/                   # BaseController, invoker, ...
│   └── shared/                  # EFIMERO: vendor de serverless/shared/
└── tests/{unit,integration}/
```

Detalle completo del formato: [.claude/rules/lambda-controller.md](../../rules/lambda-controller.md)
y [.claude/docs/lambda-controller/](../lambda-controller/).

## 6. La libreria comun vendorizada

El codigo compartido entre Lambdas vive en `serverless/shared/` (cors,
logger, rate_limit, cache, turnstile, ORM de la DB, etc.). NO se publica
como Lambda Layer.

Antes de cada `run-local`, `deploy`, `test-unit` o `test-integration`,
devtools **vendoriza** (copia) `serverless/shared/` dentro de
`<lambda>/core/shared/`. Ese `core/shared/` es efimero (`.gitignore`) y
se limpia al terminar. Los imports en el codigo del Lambda son
`from shared...` y resuelven contra el vendor.

```text
serverless/shared/   --(devtools vendoriza)-->   src/<lambda>/core/shared/
   (fuente, versionado)                            (efimero, .gitignore)
```

Asi cada Lambda empaqueta solo el codigo comun que importa, sin Layers
ni dependencias de deploy cruzadas entre stacks.

## 7. Los 4 Lambdas

| Lambda | Trigger | Memoria | Timeout | Stack |
|--------|---------|---------|---------|-------|
| `db` | `direct` (invoke directo) | 512 MB | 120s | `portfolio-db-<stage>` |
| `contact_form` | `http` `POST /contact` | 512 MB | 30s | `portfolio-contact-form-<stage>` |
| `tracking_pixel` | `http` `POST /track` | 256 MB | 10s | `portfolio-tracking-pixel-<stage>` |
| `stream_processor` | `on-table-changes` (`contacts`, `tracking`) | 512 MB | 60s | `portfolio-stream-processor-<stage>` |

### El manifiesto `lambda.yaml` (formato dev)

`lambda.yaml` describe el Lambda en terminos de DESARROLLADOR: sin ARNs,
sin politicas IAM, sin `Fn::ImportValue`. devtools lo traduce al SAM.

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
  importada (`Fn::ImportValue` de `ApiId`/`ApiRootResourceId`).
- `trigger: on-table-changes` -> Event Source Mapping por cada Stream
  importado + DLQ en `OnFailure`.
- `uses.tables` -> politica IAM scoped al ARN de cada tabla importada.
- `uses.secrets` -> `ssm:GetParameter` del path completo + `kms:Decrypt`.
- `uses.sends-email` -> `ses:SendEmail` con condition de remitente.

El `template.yaml` resultante es EFIMERO: nunca se edita ni commitea. Si
hay que cambiar la config se edita el `lambda.yaml` y se regenera con
`sam-generate`.

## 8. Stages

| Stage | Descripcion |
|-------|-------------|
| `local` | `sam local invoke` con eventos de `events/` — sin AWS |
| `dev` | Los 5 stacks desplegados en `us-east-1` (cuenta dev) |
| `stage` | Los 5 stacks desplegados (pre-produccion) |
| `prod` | Los 5 stacks desplegados (cuenta productiva) |

## 9. Region y costos

- **Region**: `us-east-1` (misma que SES production access y Neon).
- **Runtime**: Python 3.13, arm64 Graviton2.
- **Costo**: ~$0/mes — todo dentro del free tier perpetuo. Sin AWS WAF
  (rate-limit self-managed con DynamoDB), sin CloudWatch Alarms
  operacionales (solo el AWS Billing Alarm global gratis), retention de
  logs 7 dias.

---

[<- README](README.md) | [Siguiente: 02-flujos ->](02-flujos.md)
