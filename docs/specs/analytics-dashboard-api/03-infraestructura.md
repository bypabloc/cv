# 03 — Infraestructura

[< 02-arquitectura](02-arquitectura.md) | [Siguiente: 04-queries-sql >](04-queries-sql.md)

## 1. `manifest.yaml`

`serverless/lambda/services/analytics/manifest.yaml`:

```yaml
name: analytics
description: Dashboard read-only API (sessions, visits, events, contacts).

trigger:
  type: http
  method: GET
  path: /analytics

runtime: python3.13
architecture: arm64
handler: core.handler.lambda_handler

memory: 512
timeout: 30

# SnapStart Python (publica Snap por version)
snap_start: PublishedVersions

uses:
  tables:
    cache:               read-write
    rate-limit-rules:    read
    rate-limit-buckets:  read-write
  secrets:
    - neon-url

env:
  default:
    LOG_LEVEL:                       INFO
    POWERTOOLS_SERVICE_NAME:         analytics
    POWERTOOLS_METRICS_NAMESPACE:    Portfolio/Analytics
    CORS_ALLOWED_ORIGINS:            '*'
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

- `snap_start: PublishedVersions` activa SnapStart Python. devtools
  publica una version nueva en cada deploy y enlaza el alias `live`
  a esa version (mismo patron que `contact_form`).
- `architecture: arm64` -> Graviton2 (-20% costo, +19% perf vs x86_64).
- `memory: 512` MB: la query agregada mas pesada (`heatmap`) toca <100
  filas en Neon; el bottleneck es CPU JSON-serialize. 512MB da
  ~~0.5 vCPU asignado.
- `timeout: 30` s con margen — queries normales < 1s, listados con
  filtros raros < 5s. 30s es la cuota maxima del API Gateway REST.
- `tables.rate-limit-rules: read` -> el Lambda solo LEE la regla del
  endpoint; no la inserta (la insertamos via seed con la Lambda `db`).
- `tables.cache: read-write` -> `@cached` decorator necesita ambos.
- `secrets: [neon-url]` -> devtools inyecta env var
  `SSM_NEON_URL_PATH=/portfolio/<stage>/secrets/neon-url`. La Lambda lee
  el secret en runtime via `shared.db.url.resolve_database_url()`.

## 2. `pyproject.toml`

`serverless/lambda/services/analytics/pyproject.toml`:

```toml
[project]
name = "analytics"
version = "0.1.0"
description = "Dashboard read-only API for the portfolio backend."
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

CORS pre-flight: API GW REST no necesita OPTIONS si `cors_origin` se
maneja en el response del Lambda. **Excepcion**: si en el futuro el
dashboard llama desde un browser con headers custom (Authorization),
hay que agregar OPTIONS handler. Por ahora SOLO `Content-Type:
application/json` -> no necesita preflight.

## 5. Rate-limit rule

La regla `/analytics` se inserta en la tabla `rate-limit-rules` via la
Lambda `db` con un command nuevo `seed-rate-limit-rules`. Esto evita
hacer `aws dynamodb put-item` a mano.

### 5.1 Schema de la rule

Item DynamoDB en `portfolio-rate-limit-rules-<stage>`:

```json
{
  "rule_key": "/analytics",
  "kind": "ip",
  "algorithm": "sliding-window-weighted",
  "limit": 10,
  "window_seconds": 60,
  "weight_unverified": 1.0,
  "weight_verified": 0.1,
  "enabled": true,
  "description": "Dashboard API: 10 req/min/IP (sin auth, lectura)",
  "created_at": "2026-05-27T00:00:00Z",
  "updated_at": "2026-05-27T00:00:00Z"
}
```

### 5.2 Seed via Lambda `db`

Nuevo event: `serverless/lambda/services/db/events/seed_rate_limit_analytics.json`:

```json
{
  "command": "seed-rate-limit-rule",
  "args": {
    "rule_key": "/analytics",
    "kind": "ip",
    "limit": 10,
    "window_seconds": 60,
    "algorithm": "sliding-window-weighted",
    "description": "Dashboard API: 10 req/min/IP"
  }
}
```

Si la Lambda `db` aun no tiene el command `seed-rate-limit-rule`,
agregarlo en el commit de infraestructura (es ~30 LOC: parsear args,
`PutItem` con `ConditionExpression='attribute_not_exists(rule_key) OR
enabled = :true'`, devolver `{created|updated, rule_key}`).

Aplicar a cada stage:

```bash
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/seed_rate_limit_analytics.json --aws-profile=tfs-dev
python devtools/run.py serverless run --stage=stage --lambda=db \
  --event=events/seed_rate_limit_analytics.json --aws-profile=tfs-dev
python devtools/run.py serverless run --stage=prod --lambda=db \
  --event=events/seed_rate_limit_analytics.json --aws-profile=tfs-dev
```

## 6. IAM scope del rol

devtools genera el rol IAM del Lambda a partir del bloque `uses` del
manifest. Resultado esperado para `analytics`:

| Permiso | Recurso | Origen |
|---------|---------|--------|
| `dynamodb:GetItem`, `Query`, `PutItem`, `UpdateItem`, `DeleteItem` | `arn:.../portfolio-cache-<stage>` | `tables.cache: read-write` |
| `dynamodb:GetItem`, `Query` | `arn:.../portfolio-rate-limit-rules-<stage>` | `tables.rate-limit-rules: read` |
| `dynamodb:GetItem`, `Query`, `PutItem`, `UpdateItem`, `DeleteItem` | `arn:.../portfolio-rate-limit-buckets-<stage>` | `tables.rate-limit-buckets: read-write` |
| `ssm:GetParameter` | `arn:.../portfolio/<stage>/secrets/neon-url` | `secrets: [neon-url]` |
| `kms:Decrypt` | `arn:.../alias/portfolio-lambdas` | implicito (SSM SecureString) |
| `logs:CreateLogGroup`, `CreateLogStream`, `PutLogEvents` | log group del Lambda | base |
| `xray:PutTraceSegments`, `PutTelemetryRecords` | * | tracer |
| `cloudwatch:PutMetricData` | * | metrics |

Verificacion post-deploy: `aws iam get-role-policy --role-name
portfolio-analytics-<stage>-role --policy-name inline`.

## 7. SnapStart — runtime hook

`core/runtime_hooks.py` (opcional; si devtools soporta hooks vendoriza
automaticamente, ver patron `contact_form`):

```python
"""Hooks SnapStart: precalentar el grafo de imports y la validacion del
EventModel, sin tocar conexiones externas (Neon scale-to-zero las cerraria)."""

from typing import Any

from shared.lambda_kit import build_event_model
from shared.observability import logger

from core.settings.operations import OPERATIONS


def before_checkpoint(*_args: Any, **_kwargs: Any) -> None:
    """Se ejecuta una sola vez antes del snapshot SnapStart."""
    logger.info('SnapStart before_checkpoint: preloading event model')
    build_event_model(OPERATIONS, allowed_methods=('GET',))
    # NO abrir engine SQLAlchemy aqui — el restore tendria conexion DB stale.


def after_restore(*_args: Any, **_kwargs: Any) -> None:
    """Se ejecuta tras cada restore (nueva ejecucion)."""
    logger.info('SnapStart after_restore: container ready')
```

Registro de hooks: devtools lo hace via env var
`AWS_LAMBDA_EXEC_WRAPPER` o (mas comun en Python) via
`runtime_hooks.py` discovery convencional. Ver
`contact_form/core/runtime_hooks.py` como referencia.

## 8. CloudWatch — logs y metricas

- Log group: `/aws/lambda/portfolio-analytics-<stage>` retention 7d
  (default del backend).
- Metric namespace: `Portfolio/Analytics`. Metricas custom:
  - `AnalyticsQueryOk` (Count) — request exitosa
  - `AnalyticsQueryRejected` (Count) — request 4xx
  - `AnalyticsQueryError` (Count) — request 5xx
  - `AnalyticsCacheHit` / `AnalyticsCacheMiss` (Count, por action)
  - `AnalyticsColdStart` (Count, capture_cold_start_metric=True)
  - `AnalyticsRestoreDurationMs` (Milliseconds, SnapStart)
- Dimensions sugeridas: `Operation`, `Action`, `Stage`. Asi el dashboard
  futuro puede filtrar por endpoint.

NO se crean CloudWatch Alarms en este plan (politica del repo: $0/mes
sin alarms). Se agregaran cuando el dashboard sea critico.

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
5. Manual: `serverless run --stage=dev --lambda=db --event=events/seed_rate_limit_analytics.json`
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
| **Neon (queries)** | ~10 horas compute/mes (compartido con stream_processor) | $0 (free 191.9h) |
| **Total** | | **<$0.01/mes** |

El Lambda nuevo NO mueve la aguja sobre el free tier actual.

[< 02-arquitectura](02-arquitectura.md) | [Siguiente: 04-queries-sql >](04-queries-sql.md)
