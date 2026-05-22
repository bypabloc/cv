# 06 — Archivos afectados + descomposicion para paralelizacion

[<- 05 Fase D](05-fase-consumo-apps.md) | [Siguiente: commits ->](07-commits.md)

## 7. Archivos Afectados

### Crear

**Fase A — handler HTTP generico**
- `serverless/lambda/shared/lambda_kit/http_dispatch.py` — `extract_request` +
  `http_handler` + dataclass `ExtractedRequest`.
  - Verificar: `serverless tests --type=unit --shared`
- `serverless/lambda/shared/tests/unit/lambda_kit/test_extract_request_*.py`
  (5 archivos) + `test_http_handler_*.py` (4 archivos) + `_helpers.py`.
  - Verificar: `serverless tests --type=coverage --shared` (>=80%)

**Fase C — Lambda `cv`**
- `serverless/lambda/services/cv/manifest.yaml`
- `serverless/lambda/services/cv/.gitignore`
- `serverless/lambda/services/cv/pyproject.toml`
- `serverless/lambda/services/cv/core/handler.py`
- `serverless/lambda/services/cv/core/settings/{config,operations}.py`
- `serverless/lambda/services/cv/core/models/cv.py`
- `serverless/lambda/services/cv/core/services/cv_service.py`
- `serverless/lambda/services/cv/core/controllers/cv/{get,profile,experiences,projects,certificates,awards,education,languages,references,skills}.py`
- `serverless/lambda/services/cv/events/*.json`
- `serverless/lambda/services/cv/tests/**` (conftest + unit + integration)
- `serverless/lambda/shared/db/cv_repository.py` — queries de lectura del CV.
- `serverless/lambda/shared/tests/unit/db/test_cv_repository_*.py`
  - Verificar: `serverless tests --type=coverage --lambda=cv` (>=80%)
  - Verificar: `serverless run --stage=local --lambda=cv --event=events/get.json`

**Fase D — consumo apps**
- `packages/content/src/lib/cv-api-client.ts` — cliente API + validacion Zod.
  - Verificar: `pnpm --filter @portfolio/content exec vitest run`

### Modificar

**Fase A**
- `serverless/lambda/shared/lambda_kit/__init__.py` — re-exporta lo nuevo.

**Fase B**
- `serverless/lambda/services/contact_form/core/handler.py` — delega en
  `http_handler`.
  - Verificar: `serverless tests --type=unit --lambda=contact_form`
- `serverless/lambda/services/tracking_pixel/core/handler.py` — idem.
  - Verificar: `serverless tests --type=unit --lambda=tracking_pixel`
- Tests unit + integration de ambos Lambdas — nuevo contrato de entrada.
- Frontend del form de contacto (componente Astro que hace `POST /contact`) —
  enviar `operation:'contact'`, `action:'create'` en el body.
- Frontend del tracking pixel (script/componente que hace `POST /track`) —
  enviar `operation:'tracking'`, `action:'track'`.
  - Verificar: `pnpm run build` + E2E Playwright (form + tracking)

**Fase D**
- `packages/content/src/index.ts` — expone las funciones `fetch*`.
- `apps/{generic,hub,fintech,architect,leader,vibe}/scripts/build-public-assets.mjs`
  (x6) — consumen el API.
  - Verificar: `pnpm run build`

### Eliminar

`N/A` — los YAML de `packages/content/src/data/*` quedan deprecados pero NO se
borran en este plan (ver TODO de la fase D).

## 8. Descomposicion para Paralelizacion

15 tareas. Limite 5-7 agentes concurrentes. Cada tarea: File Exclusivity +
Interface Stability + Bounded Scope.

| # | Tarea | Archivos | AC | Depende de | Paraleliz. con |
|---|-------|----------|----|-----------|----|
| T1 | `http_dispatch.py` + tests | `shared/lambda_kit/http_dispatch.py`, sus tests | 1,2,3 | — | — |
| T2 | `__init__.py` re-export | `shared/lambda_kit/__init__.py` | — | T1 | — |
| T3 | Migrar `contact_form/handler.py` + tests | `contact_form/core/handler.py`, sus tests | 7 | T2 | T4,T5 |
| T4 | Migrar `tracking_pixel/handler.py` + tests | `tracking_pixel/core/handler.py`, sus tests | — | T2 | T3,T5 |
| T5 | Frontend form + tracking (operation/action) | componentes Astro form/tracking | 7 | T2 | T3,T4 |
| T6 | `cv_repository.py` + tests | `shared/db/cv_repository.py`, sus tests | 4,5,9 | T2 | — |
| T7 | Scaffold `cv`: manifest, pyproject, settings | `cv/manifest.yaml`, `pyproject.toml`, `core/settings/*` | — | T2 | T6 |
| T8 | `cv/models/cv.py` + tests | `cv/core/models/cv.py`, sus tests | 6 | T7 | T9,T10 |
| T9 | `cv_service.py` + tests | `cv/core/services/cv_service.py`, sus tests | 4,5,9 | T6,T7 | T8,T10 |
| T10 | `cv/handler.py` + `events/*.json` | `cv/core/handler.py`, `cv/events/*` | 10 | T7 | T8,T9 |
| T11 | Controllers `cv` (10 actions) + tests | `cv/core/controllers/cv/*.py`, sus tests | 4,5,6 | T8,T9 | — |
| T12 | Integration E2E `cv` | `cv/tests/integration/*` | 4,5,6,9 | T11 | — |
| T13 | `cv-api-client.ts` + barrel | `content/src/lib/cv-api-client.ts`, `index.ts` | 8 | T11 | — |
| T14 | Migrar los 6 `build-public-assets.mjs` | `apps/*/scripts/build-public-assets.mjs` | 8 | T13 | — |
| T15 | Verificacion E2E iterativa (seccion 11) | global | todos | T14 | — |

Granularidad Large: 15 tareas. T3/T4/T5 paralelizables; T8/T9/T10
paralelizables tras el scaffold.

Continua en [07-commits.md](07-commits.md).
