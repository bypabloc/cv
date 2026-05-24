# 04. Archivos afectados

> Seccion 7 del [plan-format](../../../.claude/rules/plan-format.md).
> Cada archivo lleva un comando de **verificacion** explicito.

[← 03](03-tests-requeridos.md) · [README](README.md) · [05 →](05-descomposicion-paralelizacion.md)

## Crear

### Infraestructura

- `serverless/lambda/resources/api_gateway/portfolio-api.yaml` — extender
  con campo `endpointType: EDGE` (si no existe), validacion en provisioner.
  - Verificar: `python devtools/run.py serverless tests --type=unit -- -k provisioner_supports_endpoint_type_edge`
  - Verificar: `aws apigateway get-domain-name --domain-name api.portfolio.dev.the-full-stack.com --profile tfs-dev --region us-east-1` muestra `EDGE` en `endpointConfiguration.types`.

### Backend — migration

- `serverless/lambda/shared/db/alembic/versions/b2c3d4e5f6a7_drop_stream_event_id.py` (NUEVO)
  - Verificar (en branch Neon de prueba): `alembic upgrade head` + `alembic downgrade -1` + `alembic upgrade head` sin errores.

### Backend — Lambda

- `serverless/lambda/services/tracking_pixel/tests/unit/test_track_event_model_required_page_path.py` (NUEVO)
- `serverless/lambda/services/tracking_pixel/tests/unit/test_track_event_model_required_viewport.py` (NUEVO)
- `serverless/lambda/services/tracking_pixel/tests/unit/test_track_event_model_required_utm_all.py` (NUEVO)
- `serverless/lambda/services/tracking_pixel/tests/unit/test_track_event_model_optional_referrer.py` (NUEVO)
- `serverless/lambda/services/tracking_pixel/tests/unit/test_tracking_service_persists_full_row.py` (NUEVO)
- `serverless/lambda/services/tracking_pixel/tests/unit/test_tracking_service_uses_country_meta.py` (NUEVO)
- `serverless/lambda/services/tracking_pixel/tests/unit/test_parse_ua_chrome_ios.py` (NUEVO)
- `serverless/lambda/services/tracking_pixel/tests/unit/test_parse_ua_android_webview.py` (NUEVO)
- `serverless/lambda/services/tracking_pixel/tests/unit/test_parse_ua_firefox.py` (NUEVO)
- `serverless/lambda/services/tracking_pixel/tests/unit/test_parse_ua_safari.py` (NUEVO)
- `serverless/lambda/services/tracking_pixel/tests/unit/test_parse_ua_edge.py` (NUEVO)
- `serverless/lambda/services/tracking_pixel/tests/unit/test_parse_ua_googlebot.py` (NUEVO)
- `serverless/lambda/services/tracking_pixel/tests/unit/test_handler_returns_400_when_page_path_missing.py` (NUEVO)
  - Verificar: `python devtools/run.py serverless tests --type=unit --lambda=tracking_pixel` verde, coverage per-file ≥80%.

### Shared

- `serverless/lambda/shared/tests/lambda_kit/test_http_dispatch_country_cloudfront_lower.py` (NUEVO)
- `serverless/lambda/shared/tests/lambda_kit/test_http_dispatch_country_cloudfront_upper.py` (NUEVO)
- `serverless/lambda/shared/tests/lambda_kit/test_http_dispatch_country_fallback_none.py` (NUEVO)
- `serverless/lambda/shared/tests/observability/test_ua_parser_replaces_regex_chrome.py` (NUEVO)
- `serverless/lambda/shared/tests/observability/test_ua_parser_replaces_regex_safari.py` (NUEVO)
- `serverless/lambda/shared/tests/observability/test_ua_parser_replaces_regex_bot.py` (NUEVO)
  - Verificar: `python devtools/run.py serverless tests --type=coverage --shared` verde, coverage per-file ≥80%.

### Frontend — packages/ui

- `packages/ui/src/lib/build-track-payload.ts` (NUEVO) — el constructor del
  payload, extraido de `track-event.ts` para ser unit-testable.
- `packages/ui/src/lib/stagger.ts` (NUEVO) — modulo del stagger fade-in con
  IntersectionObserver + `once: true`.
- `packages/ui/src/styles/view-transitions.css` (NUEVO) — fade default 300ms,
  stagger keyframes, reduced-motion overrides.
- `packages/ui/tests/unit/lib/build-track-payload.test.ts` (NUEVO)
- `packages/ui/tests/unit/lib/stagger.test.ts` (NUEVO)
- `packages/ui/tests/unit/components/NicheDropdown.test.ts` (NUEVO)
- `packages/ui/tests/unit/components/MobileNavDrawer.test.ts` (NUEVO)
  - Verificar: `pnpm --filter @portfolio/ui exec vitest run --coverage` verde, per-file ≥80%.

### Devtools

- `devtools/tests/unit/src/serverless/test_provisioner_supports_endpoint_type_edge.py` (NUEVO)
- `devtools/tests/unit/src/serverless/test_provisioner_recreates_domain_on_endpoint_change.py` (NUEVO)
  - Verificar: `python devtools/run.py test_runner --module=devtools --type=unit`.

### Tests feature

- `tests/feature/specs/tracking-pageview.spec.ts` (NUEVO)
- `tests/feature/specs/view-transitions.spec.ts` (NUEVO)
- `tests/feature/specs/navbar.spec.ts` (NUEVO)
  - Verificar: `python devtools/run.py test_runner --module=feature --type=feature --env=local` verde.

### Events del Lambda `db` (para deploy)

- `serverless/lambda/services/db/events/truncate-tracking.json` (NUEVO):
  ```json
  {
    "command": "truncate-table",
    "args": { "table": "tracking_events", "confirm": true }
  }
  ```
  - Verificar: el comando esta registrado en
    `serverless/lambda/services/db/core/settings/operations.py`.

### View transitions + navbar

- `packages/app-shared/src/components/HeroIdentity.astro` (NUEVO) — bloque
  `transition:name='hero-identity'` reutilizado por las pages.
  - Verificar: `pnpm exec astro check` verde.

## Modificar

### Backend — Lambda + shared

- `serverless/lambda/services/tracking_pixel/core/models/tracking.py`:
  cambiar `Optional[str/int] = None` a `str = ''` / `int = 0` con
  validators que conviertan None→default y reject de string vacio en
  campos REQUIRED segun la regla de cada uno.
  - Verificar: `python devtools/run.py serverless tests --type=unit --lambda=tracking_pixel` verde con los 13 tests nuevos.

- `serverless/lambda/services/tracking_pixel/core/services/tracking_service.py`:
  remover `stream_event_id: None` del `neon_payload`.
  - Verificar: tests anteriores + grep `rg "stream_event_id" serverless/lambda/services/tracking_pixel/` retorna 0 resultados.

- `serverless/lambda/shared/lambda_kit/http_dispatch.py`:
  agregar lectura de `cloudfront-viewer-country` con fallback a
  `cf-ipcountry`. Case-insensitive lookup.
  - Verificar: tests `test_http_dispatch_country_*` verdes.

- `serverless/lambda/shared/observability/ua_parser.py`:
  reemplazar regex custom por `ua_parser.user_agent_parser.Parse()`.
  Mantener la firma publica `parse_user_agent(ua: str) -> dict`.
  - Verificar: tests `test_ua_parser_replaces_regex_*` verdes.

- `serverless/lambda/shared/observability/pyproject.toml`:
  agregar `ua-parser` a `[project.dependencies]`.
  - Verificar: `cd serverless/lambda/shared/observability && uv lock --upgrade-package ua-parser`.

- `serverless/lambda/shared/db/models/tracking.py`:
  remover el atributo `stream_event_id`.
  - Verificar: `python -m compileall -q serverless/lambda/shared/db/models/`.

- `serverless/lambda/shared/db/repository.py`:
  el dict de columnas usado por `insert_tracking` no debe incluir
  `stream_event_id`.
  - Verificar: `python devtools/run.py serverless tests --type=coverage --shared` verde.

### Devtools — provisioner

- `devtools/serverless/provisioner.py`:
  agregar soporte para `endpointType: EDGE` en
  `api_gateway/portfolio-api.yaml`. Si el actual es REGIONAL y el yaml
  pide EDGE, recrear el custom domain (delete + create + remap base-path).
  - Verificar: tests `test_provisioner_supports_endpoint_type_edge*` verdes.
  - Verificar: `python devtools/run.py serverless tests --type=unit -- -k provisioner` verde.

### Frontend — packages/ui

- `packages/ui/src/lib/track-event.ts`:
  delegar la construccion del payload a `build-track-payload.ts`. Hook
  a `astro:page-load` en vez de `DOMContentLoaded`. Guard `firstLoad`.
  - Verificar: tests `build-track-payload.test.ts` verdes.

- `packages/ui/src/components/NicheDropdown.astro`:
  refactor del script a `AbortController` + cleanup en
  `astro:before-swap` (ver [11](11-navbar-dropdown-fix.md)).
  - Verificar: tests unit + navbar.spec desktop verdes.

- `packages/ui/src/components/MobileNavDrawer.astro`:
  reemplazar el bloque `dropdownItems` por `<details>` + `<summary>`
  (ver [11](11-navbar-dropdown-fix.md)).
  - Verificar: tests unit + navbar.spec mobile verdes.

- `packages/ui/src/lib/init-mobile-nav.ts` (si no existe, dentro del
  barrel): agregar reset de `<details>.open = false` en el evento
  `close` del `<dialog>`.
  - Verificar: navbar.spec mobile (closing drawer resets details) verde.

### Frontend — packages/app-shared

- `packages/app-shared/src/layouts/BaseLayout.astro`:
  agregar `<ClientRouter />` en `<head>`. Importar
  `view-transitions.css`.
  - Verificar: `pnpm exec astro check` + `pnpm run build` exitoso por app.

- `packages/app-shared/src/components/SitePageLayout.astro`:
  agregar slot/wrap del HeroIdentity si aplica al hero de la app.
  - Verificar: visual smoke en `pnpm run dev`.

### Apps (modificar Hero a HeroIdentity en cada app)

- `apps/generic/src/pages/index.astro` (+ /about.astro, /experience.astro si existe)
- `apps/fintech/src/pages/index.astro` (+ /about.astro si existe)
- `apps/architect/src/pages/index.astro` (+ /about.astro si existe)
- `apps/leader/src/pages/index.astro` (+ /about.astro si existe)
- `apps/vibe/src/pages/index.astro` (+ /about.astro si existe)
- `apps/hub/src/pages/index.astro` (solo home; sin /about)
  - Verificar (por app): `pnpm --filter @portfolio/<app> run build` exitoso.
  - Verificar: navbar.spec corre verde en las 6 apps.

### ThemeToggle

- `packages/ui/src/components/ThemeToggle.astro`:
  agregar script de transicion circular clip-path (ver [10](10-view-transitions-design.md)).
  - Verificar: `pnpm exec astro check` + smoke manual en Chrome.

### Project cards (si aplica)

- `packages/app-shared/src/components/ProjectCard.astro`:
  agregar `transition:name={`project-${slug}`}` al `<img>` thumbnail.
  - Verificar: `rg "transition:name" packages/app-shared/` muestra el cambio.

### Pages de detalle de proyectos (donde existan)

- `apps/<generic|fintech|architect|vibe>/src/pages/projects/[slug].astro`:
  agregar `transition:name={`project-${slug}`}` al hero image.
  - Verificar: `pnpm --filter @portfolio/<app> run build` + smoke.

## Eliminar

### Backend — codigo obsoleto

- `serverless/lambda/shared/observability/ua_parser_regex.py` (si existe
  como modulo separado) — reemplazado por `ua-parser` oficial.
  - Verificar: `rg "ua_parser_regex" serverless/` retorna 0.

- 1-2 tests obsoletos del regex parser custom (en
  `serverless/lambda/shared/tests/observability/`). El reemplazo trae
  6 tests nuevos por UA.
  - Verificar: el grep anterior + suite verde.

### View transitions / navbar

- Atributo `data-bound` en `NicheDropdown.astro` (deprecated por el
  refactor a `AbortController`).
  - Verificar: `rg "data-bound" packages/ui/src/components/NicheDropdown.astro` retorna 0.

### Plan (commit 15 — verificacion E2E)

- `docs/specs/tracking-data-completeness/` (carpeta completa):
  `git rm -r docs/specs/tracking-data-completeness/` en el ultimo
  commit.
  - Verificar: `ls docs/specs/` no muestra la carpeta.

## Resumen cuantitativo

| Categoria | Crear | Modificar | Eliminar |
|-----------|-------|-----------|----------|
| Infra (yaml) | 0 | 1 | 0 |
| Lambda code | 0 | 5 | 1 |
| Lambda tests | 13 | 0 | 1-2 |
| Shared code | 0 | 3 | 0 |
| Shared tests | 6 | 0 | 0 |
| Devtools code | 0 | 1 | 0 |
| Devtools tests | 2 | 0 | 0 |
| Frontend code | 4 | 8-12 (pages) | 0 |
| Frontend tests | 4 | 0 | 0 |
| Feature E2E | 3 | 0 | 0 |
| Events Lambda db | 1 | 0 | 0 |
| Plan | 0 | 0 | 1 (carpeta) |
| **Total** | **33** | **18-22** | **3-4** |

Plan **Large** confirmado (55+ archivos tocados).

---

Siguiente: [05. Descomposicion para paralelizacion →](05-descomposicion-paralelizacion.md)
