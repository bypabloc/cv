# 03 — Infraestructura

[< 02-arquitectura](02-arquitectura.md) | [Siguiente: 04-queries-sql >](04-queries-sql.md)

## 1. `manifest.yaml`

`serverless/lambda/services/analytics/manifest.yaml`:

```yaml
name: analytics
description: Admin metrics read-only API (sessions, visits, events, contacts), JWT-authed.

trigger:
  type: http
  method: GET
  path: /analytics

runtime: python3.13
architecture: arm64
handler: core.handler.lambda_handler

memory: 512
timeout: 30

# SnapStart Python (true = devtools publica version + alias :live)
snap_start: true

uses:
  tables:
    cache:               read-write
    rate-limit-rules:    read
    rate-limit-buckets:  read-write
  secrets:
    - neon-url
    - jwt-secret

env:
  default:
    LOG_LEVEL:                       INFO
    POWERTOOLS_SERVICE_NAME:         analytics
    POWERTOOLS_METRICS_NAMESPACE:    Portfolio/Analytics
    # CORS: refleja el Origin del admin (echo) — NUNCA '*'. http_handler
    # resuelve el origen permitido contra esta lista.
    CORS_ALLOWED_ORIGINS:            'https://admin.portfolio.dev.the-full-stack.com,https://admin.portfolio.stage.the-full-stack.com,https://admin.portfolio.the-full-stack.com'
    RATE_LIMIT_ENDPOINT:             '/analytics'
    ANALYTICS_DATE_DEFAULT_DAYS:     '30'
    ANALYTICS_DATE_MAX_DAYS:         '90'
    ANALYTICS_PAGE_SIZE_DEFAULT:     '50'
    ANALYTICS_PAGE_SIZE_MAX:         '200'
    ANALYTICS_CACHE_TTL_AGGREGATE:   '60'
    ANALYTICS_CACHE_TTL_LIVE:        '10'

  stage:
    dev:
      LOG_LEVEL: INFO
    stage:
      LOG_LEVEL: INFO
    prod:
      LOG_LEVEL: WARNING
```

Notas:

- `snap_start: true` habilita SnapStart Python. devtools publica una
  version nueva en cada deploy y enlaza el alias `:live` a esa version
  (mismo patron que `contact_form`). El valor es un booleano; el
  provisioner internamente configura `PublishedVersions` en la API de AWS.
- `architecture: arm64` -> Graviton2 (-20% costo, +19% perf vs x86_64).
- `memory: 512` MB: la query agregada mas pesada (`heatmap`) toca <100
  filas en Neon; el bottleneck es CPU JSON-serialize. 512MB da
  ~~0.5 vCPU asignado.
- `timeout: 30` s con margen — queries normales < 1s, listados con
  filtros raros < 5s. 30s es la cuota maxima del API Gateway REST.
- `tables.rate-limit-rules: read` -> el Lambda solo LEE la regla del
  endpoint; no la inserta (la insertamos via seed con la Lambda `db`).
- `tables.cache: read-write` -> `@cached` decorator necesita ambos.
- `secrets: [neon-url, jwt-secret]`:
  - `neon-url` -> devtools inyecta env var
    `SSM_NEON_URL_PATH=/portfolio/<stage>/neon-url`. La Lambda lee
    el secret en runtime via `shared.db.url.resolve_database_url()`.
  - `jwt-secret` -> devtools inyecta env var
    `SSM_JWT_SECRET_PATH=/portfolio/<stage>/jwt-secret`. La Lambda lo lee
    en cold start (mismo patron que el Lambda `auth`) para validar la firma
    HS256 del access JWT. Ambos son `SecureString` cifrados con
    `alias/portfolio-lambdas` -> requieren `kms:Decrypt`.
- `CORS_ALLOWED_ORIGINS` NO es `'*'`: lista los hostnames del admin por env
  (`admin.portfolio.{dev,stage,}.the-full-stack.com`). `http_handler` con
  `cors_origin='echo'` refleja el Origin solo si esta en la lista.

## 2. `pyproject.toml`

`serverless/lambda/services/analytics/pyproject.toml`:

```toml
[project]
name = "analytics"
version = "0.1.0"
description = "Admin metrics read-only API (JWT-authed) for the portfolio backend."
requires-python = ">=3.13,<3.14"
dependencies = []

[dependency-groups]
dev = [
    "pytest>=8.3,<9",
    "pytest-cov>=5.0,<6",
    "pytest-mock>=3.14,<4",
    "hypothesis>=6.103,<7",
]
```

Reglas:

- `dependencies = []` (regla D-3): TODA dep externa la aporta el cierre
  transitivo de `shared/`. `serverless lint-deps --lambda=analytics`
  debe dar exit 0.
- Grupo `dev` solo con framework de testing — NO infra de runtime.

## 3. Eventos de ejemplo (`events/`)

Un JSON por action para `serverless run --event=events/<X>.json`. Shape:

```json
{
  "httpMethod": "GET",
  "path": "/analytics",
  "queryStringParameters": {
    "operation": "analytics",
    "action": "overview",
    "from": "2026-04-27",
    "to": "2026-05-27"
  },
  "headers": {
    "x-forwarded-for": "203.0.113.42",
    "cloudfront-viewer-country": "AR",
    "user-agent": "curl/8.0"
  },
  "requestContext": {
    "requestId": "test-overview-001",
    "identity": {"sourceIp": "203.0.113.42"}
  },
  "body": null,
  "isBase64Encoded": false
}
```

19 eventos en total (uno por action). En el plan se crean con un script
helper en `tests/conftest.py` para no replicar a mano.

## 4. API Gateway

`serverless/lambda/resources/api_gateway/portfolio-api.yaml` NO se
modifica. El `provisioner` de devtools agrega automaticamente el metodo
`GET /analytics` al leer `trigger.method` + `trigger.path` del manifest.

CORS pre-flight: la UI de metricas (browser, en
`admin.portfolio.{env}.the-full-stack.com`) envia el header custom
`Authorization: Bearer <JWT>`, lo que dispara un preflight `OPTIONS`. Por
eso hay que agregar un OPTIONS handler para `/analytics` que responda
`Access-Control-Allow-Headers: Content-Type, Authorization` +
`Access-Control-Allow-Origin: <Origin admin permitido>` (echo desde la
lista `CORS_ALLOWED_ORIGINS`). NO usar `'*'` en el preflight (incompatible
con credenciales y con la lista restringida de origenes del admin).

## 5. Rate-limit rule

La regla `/analytics` se inserta en la tabla `rate-limit-rules` usando
el CLI existente de devtools (`devtools/serverless/rate_limit_cmds.py`).
No se crea ningun command nuevo en la Lambda `db`.

### 5.1 Schema de la rule

Item DynamoDB en `portfolio-rate-limit-rules-<stage>` (schema real de
`shared/rate_limit/rules.py`):

```json
{
  "rule_key": "endpoint#/analytics",
  "kind": "endpoint",
  "limit": 10,
  "window_seconds": 60,
  "action": "throttle",
  "expires_at": null,
  "reason": "Analytics API: 10 req/min por endpoint (segunda capa tras el JWT)",
  "metadata": {}
}
```

Notas:
- `rule_key` lleva el prefijo `endpoint#` (formato real de `rules.py`).
- `kind` es `'endpoint'`, no `'ip'` (el algoritmo sliding-window-weighted
  es interno de `check.py`; no se expone en la rule).
- No existen los campos `algorithm`, `weight_unverified`, `weight_verified`
  en el schema real.

### 5.2 Seed via CLI de devtools

```bash
python devtools/run.py serverless rate-limit set \
  --endpoint=/analytics --limit=10 --window=60 --stage=dev \
  --aws-profile=tfs-dev

python devtools/run.py serverless rate-limit set \
  --endpoint=/analytics --limit=10 --window=60 --stage=stage \
  --aws-profile=tfs-dev

python devtools/run.py serverless rate-limit set \
  --endpoint=/analytics --limit=10 --window=60 --stage=prod \
  --aws-profile=tfs-dev
```

El comando es idempotente (upsert). En runtime el Lambda llama
`get_endpoint_rule('/analytics')` para leer la regla.

## 6. IAM scope del rol

devtools genera el rol IAM del Lambda a partir del bloque `uses` del
manifest. Resultado esperado para `analytics`:

| Permiso | Recurso | Origen |
|---------|---------|--------|
| `dynamodb:GetItem`, `Query`, `PutItem`, `UpdateItem`, `DeleteItem` | `arn:.../portfolio-cache-<stage>` | `tables.cache: read-write` |
| `dynamodb:GetItem`, `Query` | `arn:.../portfolio-rate-limit-rules-<stage>` | `tables.rate-limit-rules: read` |
| `dynamodb:GetItem`, `Query`, `PutItem`, `UpdateItem`, `DeleteItem` | `arn:.../portfolio-rate-limit-buckets-<stage>` | `tables.rate-limit-buckets: read-write` |
| `ssm:GetParameter` | `arn:.../portfolio/<stage>/neon-url` | `secrets: [neon-url]` |
| `ssm:GetParameter` | `arn:.../portfolio/<stage>/jwt-secret` | `secrets: [jwt-secret]` (validar HS256) |
| `kms:Decrypt` | `arn:.../alias/portfolio-lambdas` | implicito (ambos SSM SecureString: neon-url + jwt-secret) |
| `logs:CreateLogGroup`, `CreateLogStream`, `PutLogEvents` | log group del Lambda | base |
| `cloudwatch:PutMetricData` | * | metrics |

Verificacion post-deploy: `aws iam get-role-policy --role-name
portfolio-analytics-<stage>-role --policy-name inline`.

## 7. SnapStart — precalentamiento en el INIT

El patron del backend (cv, contact_form) NO usa `runtime_hooks.py` con
`before_checkpoint`/`after_restore`. El precalentamiento se hace en el
module-scope del `core/handler.py`, de modo que quede capturado en el
snapshot de SnapStart.

En `core/handler.py`, inmediatamente tras los imports de modulos de modelos:

```python
# Precalentamiento INIT para SnapStart — patron identico a cv y contact_form.
# warm_db() es best-effort (try/except interno): precalienta el engine
# NullPool + configure_mappers sin abrir conexion a Neon (NullPool no
# conecta en el INIT; las conexiones no sobreviven al snapshot).
import shared.db.models.visitor.session          # noqa: F401
import shared.db.models.visitor.session_visit    # noqa: F401
import shared.db.models.visitor.tracking         # noqa: F401
import shared.db.models.visitor.contact          # noqa: F401
import shared.db.models.taxonomy.event_type      # noqa: F401

from shared.db.warmup import warm_db
warm_db()
```

Esto registra el mapper SQLAlchemy completo del dominio visitor en el
snapshot. El restore de SnapStart no paga el costo de `configure_mappers`
en la primera invocacion post-restore.

## 8. CloudWatch — logs y metricas

- Log group: `/aws/lambda/portfolio-analytics-<stage>` retention 7d
  (default del backend).
- Metric namespace: `Portfolio/Analytics`. Metricas custom:
  - `AnalyticsQueryOk` (Count) — request exitosa
  - `AnalyticsQueryRejected` (Count) — request 4xx
  - `AnalyticsQueryError` (Count) — request 5xx
  - `AnalyticsCacheHit` / `AnalyticsCacheMiss` (Count, por action)
  - `AnalyticsColdStart` (Count, capture_cold_start_metric=True)
- Dimensions sugeridas: `Operation`, `Action`, `Stage`. Asi la UI de
  metricas puede filtrar por endpoint.

NO se crean CloudWatch Alarms en este plan (politica del repo: $0/mes
sin alarms). Se agregaran cuando las metricas del admin sean criticas.

## 9. CI/CD impacto

`.github/workflows/deploy-backend.yml` ya auto-detecta Lambdas nuevos al
escanear `serverless/lambda/services/*/manifest.yaml`. No hace falta
editar el workflow.

**Flujo esperado** tras mergear el plan a `dev`:

1. `branch-flow-guard.yml` aprueba (es PR a `dev`).
2. `migrate-db` corre Alembic — sin migrations nuevas para este plan
   (no se modifica Neon).
3. `detect-changes` lista `analytics` (carpeta nueva).
4. `deploy-lambdas` matrix: aplica el deploy del nuevo Lambda a `dev`.
5. Manual: `python devtools/run.py serverless rate-limit set --endpoint=/analytics --limit=10 --window=60 --stage=dev`
   para insertar la rule (la rule NO se versiona en codigo, vive en
   DynamoDB).
6. Smoke E2E (curl) contra `api.portfolio.dev.the-full-stack.com/analytics`.

Promocion a `stage` y `prod` con el flujo normal (PR `dev -> stage` y
`stage -> main`).

## 10. Cost estimation

| Item | Calculo | Costo/mes |
|------|---------|-----------|
| Lambda invocations | ~10 req/dia * 30 = 300 req/mes (free tier: 1M) | $0 |
| Lambda GB-sec | 0.5 GB * 1s * 300 = 150 GB-sec/mes (free: 400k) | $0 |
| API Gateway REST | 300 req/mes * $3.50/M | <$0.01 |
| DynamoDB writes (cache + rate-limit buckets) | ~600 writes/mes | $0 (free) |
| DynamoDB reads (cache hits + rules) | ~600 reads/mes | $0 (free) |
| CloudWatch Logs | ~5 MB/mes | $0 (free 5GB) |
| **Neon (queries)** | ~10 horas compute/mes (compartido con cv, auth, contact_form) | $0 (free 191.9h) |
| **Total** | | **<$0.01/mes** |

El Lambda nuevo NO mueve la aguja sobre el free tier actual.

[< 02-arquitectura](02-arquitectura.md) | [Siguiente: 04-queries-sql >](04-queries-sql.md)
