# SPEC-001: SAM template base + 3 tablas DynamoDB hot path

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: `serverless/template.yaml`, `serverless/samconfig.toml`,
`serverless/pyproject.toml`, `serverless/Makefile`
**Dependencias**: SPEC-000
**Paralelizable con**: SPEC-011

## 1. Contexto

Necesitamos el SAM template skeleton del proyecto antes de implementar
cualquier Lambda. Define recursos comunes: API Gateway REST, las 3 tablas
DynamoDB de hot path (`contacts`, `tracking`, `cache`), Layer
`common_python` con Powertools, y `Globals` de Lambda (Python 3.13 arm64,
tracing, log retention 7d).

### Hallazgos de exploracion

- Patron documentado: `serverless/ARCHITECTURE.md` seccion 7 (template
  resources high-level)
- Cuando termine SPEC-001, queda deployable un stack base "vacio" (sin
  Lambdas) en stage `dev`
- AWS::Serverless::Function `Globals` simplifica configuracion repetida

## 2. Solucion propuesta

Crear `serverless/template.yaml` con SAM transform + 6 recursos base:

1. `AWS::Serverless::LayerVersion` `CommonLayer` (Powertools v3 + httpx + pydantic)
2. `AWS::Serverless::Api` `PortfolioApi` (REST, CORS whitelist, JSON validators)
3. `AWS::DynamoDB::Table` `ContactsTable` (PK=id, Streams habilitado, PITR)
4. `AWS::DynamoDB::Table` `TrackingTable` (PK=session_id, SK=page_id, TTL, Streams)
5. `AWS::DynamoDB::Table` `CacheTable` (PK=cache_key, TTL, sin Streams)
6. `AWS::Logs::LogGroup` para `AccessLogGroup` del API GW (retention 7d)

Plus archivos auxiliares: `samconfig.toml` con stages `dev`/`prod`,
`pyproject.toml` con deps Python para tests, `Makefile` con atajos.

### Decisiones clave

- **Decision 1: Globals.Function** — Runtime python3.13, Architectures
  [arm64], Tracing Active, Layers [CommonLayer], LogRetentionInDays 7,
  Environment variables Powertools comunes. Centralizado para no repetir
  en cada Function.
- **Decision 2: API Gateway REST (no HTTP)** — confirmado en
  `.claude/docs/aws-api-gateway/01-architecture.md`. REST permite usage
  plans + request validators (perdidos en HTTP API).
- **Decision 3: CORS via `Cors:` shortcut** — para metodos 2XX. Errores
  4XX/5XX requieren Gateway Responses manuales (esto va en SPEC-005/006).

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given `serverless/template.yaml` creado, When ejecuto
  `serverless validate`, Then output = `template.yaml is a valid SAM
  Template`
- **AC-2**: Given `samconfig.toml` con stage `dev`, When ejecuto
  `serverless build`, Then directorio `.aws-sam/build/` existe y contiene
  Layer + tablas (CloudFormation transformado correctamente)
- **AC-3**: Given AWS credentials configuradas, When ejecuto
  `serverless deploy --stage=dev --guided` y completo prompts, Then el
  stack `portfolio-backend-dev` se crea exitosamente y outputs incluyen
  `ApiEndpoint`, `ContactsTableName`, `TrackingTableName`, `CacheTableName`
- **AC-4**: Given stack desplegado, When ejecuto
  `aws dynamodb describe-table --table-name <ContactsTableName>`, Then
  `StreamSpecification.StreamEnabled: true` y `StreamViewType:
  NEW_AND_OLD_IMAGES`
- **AC-5**: Given stack desplegado, When ejecuto `aws dynamodb
  describe-time-to-live --table-name <TrackingTableName>`, Then
  `TimeToLiveDescription.AttributeName: expires_at` y `TimeToLiveStatus:
  ENABLED`
- **AC-6**: Given stack desplegado y un OPTIONS preflight a
  `<ApiEndpoint>/contact`, When inspecciono headers de respuesta, Then
  incluye `Access-Control-Allow-Origin: https://the-full-stack.com` y
  status 200

## 4. Diagrama de Flujo

N/A — infra setup, sin flujo de datos todavia.

## 5. Diagrama ER

```text
                +------------------+
                |  ContactsTable   |
                +------------------+
                | PK: id (S)       |
                | Streams: enabled |
                | PITR: enabled    |
                +------------------+

                +-------------------+
                |  TrackingTable    |
                +-------------------+
                | PK: session_id(S) |
                | SK: page_id (S)   |
                | TTL: expires_at   |
                | Streams: enabled  |
                +-------------------+

                +------------------+
                |  CacheTable      |
                +------------------+
                | PK: cache_key (S)|
                | TTL: expires_at  |
                +------------------+
```

## 6. Tests Requeridos

### 6.C. Typecheck

- `cfn-lint serverless/template.yaml` (opcional pero recomendado)

### 6.E. Manual verification

- `serverless validate` + `serverless build` + `serverless deploy --stage=dev`
- `aws dynamodb describe-table` para las 3 tablas
- curl OPTIONS preflight contra API endpoint

## 7. Archivos Afectados

### Crear

- `serverless/template.yaml` — SAM template completo con 6 recursos base
  - Verificar: `serverless validate` pasa (AC-1)
- `serverless/samconfig.toml` — config por stage (dev, prod)
  - Verificar: `cat serverless/samconfig.toml | grep config_env` lista 2 envs
- `serverless/pyproject.toml` — deps Python para tests (pytest, moto, responses)
  - Verificar: `uv sync --project serverless` exitoso
- `serverless/uv.lock` — generado por uv sync
- `serverless/Makefile` — atajos `make validate build deploy logs clean`
  - Verificar: `make validate` ejecuta `serverless validate`
- `serverless/.gitignore` — `.aws-sam/`, `.venv/`, `samconfig.toml.local`,
  `*.zip`, `env/.env.dev`, `env/.env.prod`
- `serverless/src/layers/common_python/requirements.txt` —
  `aws-lambda-powertools[all]>=3.0` + `httpx>=0.27` + `pydantic>=2.0`
  - Verificar: `serverless build` empaqueta layer correctamente

### Modificar

- Nada (carpeta nueva).

## 8. Descomposicion para Paralelizacion

N/A — Small/Medium spec, no requiere paralelizacion.

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-000 completada (AWS CLI + SSM secrets + Turnstile widget)
- [ ] AWS SAM CLI v1.130+ instalado (`sam --version`)
- [ ] uv >= 0.4 instalado (`uv --version`)

### Definition of Done

- [ ] AC-1 a AC-6 cumplidos
- [ ] Output de `serverless deploy --stage=dev` registrado en
      `serverless/docs/deployment-outputs-dev.md` (apiEndpoint, table
      names) — gitignored
- [ ] CloudWatch Logs `AccessLogGroup` retention=7
- [ ] `Globals.Function.Tracing: Active` (X-Ray habilitado)
- [ ] Tagging: todos los recursos con `Project=portfolio, ManagedBy=SAM`
- [ ] Commit en branch `feature/spec-001-sam-base`
- [ ] PR contra `dev` con descripcion linkeando SPEC-001
