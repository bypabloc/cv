# 05. Descomposicion para paralelizacion

> Seccion 8 del [plan-format](../../../.claude/rules/plan-format.md).
> Cada tarea pasa los 3 checks (File Exclusivity, Interface Stability,
> Bounded Scope) y lleva 6 campos (Archivos / AC / Depende de /
> Paralelizable con / Verify / Done).

[← 04](04-archivos-afectados.md) · [README](README.md) · [06 →](06-commits.md)

## Mapa de tareas (15)

```text
T0 (base secuencial)
   |
T1 (provisioner EDGE) ──┬─ T2 (dev domain)
                        ├─ T3 (stage domain)
                        └─ T4 (prod domain)
   |
T5 (drop stream_event_id migration)
   |
T6 (Pydantic required + tests rojos)
   |
T7 (ua-parser swap) ──── T8 (cloudfront-viewer-country)
   |
T9 (build-track-payload extract + tests) ─┐
T10 (ClientRouter + view-transitions.css) ─┼─ paralelo
T11 (NicheDropdown + MobileNavDrawer fix) ─┤
T12 (HeroIdentity + ProjectCard transitions) ┘
   |
T13 (Playwright: tracking + view + navbar)
   |
T14 (deploy + truncate + verify E2E final)
```

## T0 — Base secuencial: carpeta del plan

- **Archivos**: `docs/specs/tracking-data-completeness/{README.md, 01-..., 02-..., 03-..., 04-..., 05-..., 06-..., 07-..., 08-..., 09-..., 10-..., 11-...}.md` (12 archivos)
- **AC referenciados**: ninguno (planificacion)
- **Depende de**: `dev` actualizada
- **Paralelizable con**: nada (es la base secuencial)
- **Verify**: `ls docs/specs/tracking-data-completeness/` lista los 12 archivos
- **Done**: commit `docs(specs): plan tracking-data-completeness` en `feature/tracking-data-completeness`

## T1 — Provisioner soporta `endpointType: EDGE`

- **Archivos**: `devtools/serverless/provisioner.py`, `devtools/tests/unit/src/serverless/test_provisioner_supports_endpoint_type_edge.py`, `test_provisioner_recreates_domain_on_endpoint_change.py`, `serverless/lambda/resources/api_gateway/portfolio-api.yaml`
- **AC**: AC-8 (parcial)
- **Depende de**: T0
- **Paralelizable con**: T5, T6 (toca codigo diferente)
- **Verify**: `python devtools/run.py test_runner --module=devtools --type=unit -- -k provisioner_supports_endpoint_type_edge` verde
- **Done**: commit `chore(devtools): provisioner soporta endpointType=EDGE`

## T2 — Recrear `api.portfolio.dev` Edge-Optimized

- **Archivos**: solo SSM y AWS (no codigo). Estado local actualizado en `serverless/lambda/.state/portfolio-api-dev.json`.
- **AC**: AC-8 (dev)
- **Depende de**: T1
- **Paralelizable con**: T3, T4 (envs independientes, AWS API resources separados)
- **Verify**:
  ```bash
  aws apigateway get-domain-name --domain-name api.portfolio.dev.the-full-stack.com --profile tfs-dev | jq '.endpointConfiguration.types[0]'
  # debe imprimir "EDGE"
  curl -X POST https://api.portfolio.dev.the-full-stack.com/track -d '{}' -H 'Content-Type: application/json'
  # debe responder HTTP 400 (validation), NO 5xx ni timeout
  ```
- **Done**: commit `feat(infra): api.portfolio.dev → Edge-Optimized`

## T3 — Recrear `api.portfolio.stage` Edge-Optimized

- **Archivos**: idem T2 para stage
- **AC**: AC-8 (stage)
- **Depende de**: T1
- **Paralelizable con**: T2, T4
- **Verify**: idem T2 con dominio `stage`
- **Done**: commit `feat(infra): api.portfolio.stage → Edge-Optimized`

## T4 — Recrear `api.portfolio` (prod) Edge-Optimized

- **Archivos**: idem T2 para prod
- **AC**: AC-8 (prod)
- **Depende de**: T1
- **Paralelizable con**: T2, T3
- **Verify**: idem T2 con dominio prod + canary curl desde el frontend
- **Done**: commit `feat(infra): api.portfolio (prod) → Edge-Optimized`

> **Decision operativa**: T2/T3/T4 se hacen en una unica ventana con
> DNS TTL bajado a 60s ≥10min antes. Aunque cada env va en su commit,
> el deploy del custom domain en AWS NO se hace hasta la fase 14
> (capitulo [08](08-verificacion-e2e.md)). El commit registra la
> intencion (state local actualizado); la aplicacion real ocurre via
> `serverless provision-infra --aws-profile=tfs-dev --stage=<env>`.

## T5 — Drop `stream_event_id` (DB + modelo + repo)

- **Archivos**: `serverless/lambda/shared/db/alembic/versions/b2c3d4e5f6a7_drop_stream_event_id.py`, `serverless/lambda/shared/db/models/tracking.py`, `serverless/lambda/shared/db/repository.py`, `serverless/lambda/services/tracking_pixel/core/services/tracking_service.py`
- **AC**: AC-5
- **Depende de**: T0
- **Paralelizable con**: T1, T6, T7, T8 (toca DB y service del Lambda; no toca infra ni frontend)
- **Verify**:
  - `python -m compileall -q serverless/lambda/shared/db/`
  - En branch Neon de prueba: `alembic upgrade head` + `alembic downgrade -1` + `alembic upgrade head` verde
  - `rg "stream_event_id" serverless/` retorna 0 resultados
- **Done**: commit `refactor(db): drop stream_event_id de tracking_events`

## T6 — Pydantic TrackEventModel required + tests rojos

- **Archivos**: `serverless/lambda/services/tracking_pixel/core/models/tracking.py`, `tests/unit/test_track_event_model_required_page_path.py`, `test_track_event_model_required_viewport.py`, `test_track_event_model_required_utm_all.py`, `test_track_event_model_optional_referrer.py`, `test_tracking_service_persists_full_row.py`, `test_handler_returns_400_when_page_path_missing.py`
- **AC**: AC-1, AC-2, AC-9
- **Depende de**: T0 (T5 es paralelo — la columna `stream_event_id` ya fue droppeada O se hace en paralelo sin colision por archivos)
- **Paralelizable con**: T1, T5 (archivos disjuntos)
- **Verify**:
  - Tests rojos antes del cambio (TDD): correr la suite, confirmar fallos esperados
  - Implementar el cambio en Pydantic
  - Tests verdes: `python devtools/run.py serverless tests --type=unit --lambda=tracking_pixel`
  - Coverage per-file ≥80%
- **Done**: commit `feat(lambda): TrackEventModel exige 9 campos required`

## T7 — UA parser swap (regex → ua-parser)

- **Archivos**: `serverless/lambda/shared/observability/ua_parser.py`, `serverless/lambda/shared/observability/pyproject.toml`, 6 tests nuevos `test_parse_ua_*.py`, 3 tests `test_ua_parser_replaces_regex_*.py`
- **AC**: AC-4
- **Depende de**: T0
- **Paralelizable con**: T1, T5, T6, T8 (toca solo shared/observability)
- **Verify**:
  - `cd serverless/lambda/shared/observability && uv sync` (instala `ua-parser`)
  - `python devtools/run.py serverless tests --type=coverage --shared` verde
  - `rg "_PARSER_REGEX" serverless/lambda/shared/observability/` retorna 0
- **Done**: commit `refactor(lambda): ua-parser oficial reemplaza regex custom`

## T8 — `cloudfront-viewer-country` en http_dispatch

- **Archivos**: `serverless/lambda/shared/lambda_kit/http_dispatch.py`, 3 tests `test_http_dispatch_country_*.py`, 1 test `test_tracking_service_uses_country_meta.py`
- **AC**: AC-3
- **Depende de**: T0
- **Paralelizable con**: T1, T5, T6, T7
- **Verify**: tests `country` verdes en unit + coverage
- **Done**: commit `feat(lambda): leer country de cloudfront-viewer-country`

## T9 — build-track-payload + tests (frontend)

- **Archivos**: `packages/ui/src/lib/build-track-payload.ts`, `packages/ui/src/lib/track-event.ts` (delegar), `packages/ui/tests/unit/lib/build-track-payload.test.ts`
- **AC**: AC-1, AC-2, AC-6, AC-9
- **Depende de**: T0
- **Paralelizable con**: T10, T11, T12 (archivos exclusivos de cada uno)
- **Verify**:
  - `pnpm --filter @portfolio/ui exec vitest run --coverage` verde, per-file ≥80%
  - `pnpm exec biome check packages/ui/` verde
  - `pnpm exec tsc --noEmit` verde
- **Done**: commit `feat(frontend): build-track-payload con 9 campos required`

## T10 — ClientRouter + view-transitions.css

- **Archivos**: `packages/app-shared/src/layouts/BaseLayout.astro`, `packages/ui/src/styles/view-transitions.css`, `packages/ui/src/lib/stagger.ts`, `packages/ui/tests/unit/lib/stagger.test.ts`, `packages/ui/src/components/ThemeToggle.astro` (script clip-path)
- **AC**: AC-7, AC-11
- **Depende de**: T0
- **Paralelizable con**: T9, T11, T12
- **Verify**:
  - `pnpm exec astro check` verde
  - `pnpm run build` exitoso en las 6 apps
  - Tests stagger verdes en Vitest
  - Smoke visual: `pnpm run dev`, navegar entre /home y /experience, ver fade
- **Done**: commit `feat(frontend): habilitar ClientRouter + view transitions globales`

## T11 — Navbar fix (NicheDropdown + MobileNavDrawer)

- **Archivos**: `packages/ui/src/components/NicheDropdown.astro`, `packages/ui/src/components/MobileNavDrawer.astro`, `packages/ui/src/lib/init-mobile-nav.ts` (o equivalente), `packages/ui/tests/unit/components/NicheDropdown.test.ts`, `MobileNavDrawer.test.ts`
- **AC**: AC-12, AC-13
- **Depende de**: T0 (T10 es paralelo — el fix usa `astro:before-swap` que existe aunque ClientRouter no este activo aun; sin colision)
- **Paralelizable con**: T9, T10, T12
- **Verify**:
  - Tests unit verdes
  - `pnpm exec astro check` verde
  - Smoke manual desktop + mobile
- **Done**: commit `fix(ui): NicheDropdown AbortController + drawer details colapsable`

## T12 — HeroIdentity + ProjectCard `transition:name`

- **Archivos**: `packages/app-shared/src/components/HeroIdentity.astro`, `packages/app-shared/src/components/ProjectCard.astro` (modificar), 8-12 pages de las apps (`/index.astro`, `/about.astro`, `/projects/[slug].astro` donde aplique)
- **AC**: AC-11
- **Depende de**: T10 (necesita view-transitions habilitadas)
- **Paralelizable con**: T9, T11 (archivos disjuntos)
- **Verify**:
  - `pnpm run build` exitoso por app
  - `rg "transition:name" apps/ packages/` muestra solo `hero-identity` y `project-{slug}`
  - Smoke visual: navegar entre /home y /about, ver hero morph
- **Done**: commit `feat(frontend): HeroIdentity + ProjectCard con transition:name`

## T13 — Playwright E2E (tracking + view-transitions + navbar)

- **Archivos**: `tests/feature/specs/tracking-pageview.spec.ts`, `view-transitions.spec.ts`, `navbar.spec.ts`
- **AC**: AC-2, AC-6, AC-9, AC-11, AC-12, AC-13, AC-14
- **Depende de**: T9, T10, T11, T12 (todo el frontend mergeado)
- **Paralelizable con**: nada (depende de todo el frontend)
- **Verify**:
  ```bash
  python devtools/run.py docker up --env=local
  python devtools/run.py test_runner --module=feature --type=feature --env=local
  ```
  3 specs en verde, 6 apps cada uno.
- **Done**: commit `test(feature): E2E para tracking + view-transitions + navbar`

## T14 — Deploy + migration + truncate + verificacion E2E final

- **Archivos**: solo events JSON + state local. No commits de codigo
  productivo (todo ya commiteado en T2-T13).
- **AC**: AC-2, AC-3, AC-5, AC-8 (verificacion en cloud)
- **Depende de**: T2, T3, T4, T5, T6, T7, T8, T13
- **Paralelizable con**: nada (cierre del plan)
- **Verify**: bateria del capitulo [08](08-verificacion-e2e.md):
  - `serverless provision-infra --aws-profile=tfs-dev --stage=dev` aplica EDGE
  - `serverless run --lambda=db --event=events/migrate.json --stage=dev` aplica migration
  - `serverless run --lambda=db --event=events/truncate-tracking.json --stage=dev`
  - `serverless deploy --lambda=tracking_pixel --stage=dev` (re-deploy con ua-parser)
  - Smoke: navegar el portfolio dev, ver 1 fila completa en Neon (11 columnas no-null)
  - Repetir para stage y prod
  - `pnpm exec biome check . && pnpm exec tsc --noEmit && pnpm exec astro check && pnpm exec vitest run --coverage && pnpm run build && pnpm exec playwright test`
  - **TODOS verdes**
- **Done**: commit `chore(plan): verificacion E2E + git rm -r docs/specs/tracking-data-completeness/`

## Checks de paralelizabilidad

| Tarea | File Exclusivity | Interface Stability | Bounded Scope |
|-------|------------------|--------------------|---------------|
| T2-T4 (envs) | Si: cada env tiene su `.state/portfolio-api-<env>.json` | Si: no cambia API publica | Si: 1 env por tarea |
| T5 vs T6 | Si: T5 toca `shared/db/`, T6 toca `services/tracking_pixel/core/models/` | Si: insert_tracking signature estable | Si |
| T7 vs T8 | Si: T7 toca `observability/`, T8 toca `lambda_kit/` | Si | Si |
| T9 vs T10 | Si: T9 toca `lib/`, T10 toca `layouts/` y `styles/` y `components/ThemeToggle.astro` | Si: `buildTrackPayload` export estable | Si |
| T10 vs T11 | Si: T10 toca `BaseLayout` y `view-transitions.css`, T11 toca `NicheDropdown.astro` y `MobileNavDrawer.astro` | Si | Si |
| T11 vs T12 | Si: T11 toca `NicheDropdown`/`MobileNavDrawer`, T12 toca `HeroIdentity` y `ProjectCard` y pages | Si | Si |

## Granularidad

15 tareas, plan Large. Cada tarea es ≤ 5 archivos modificados (excepto
T12 que toca pages de 5 apps — toleramos porque las 5 son cambios
identicos copy-paste, sin riesgo). Limite de 5-7 agentes concurrentes
respetado: las fases paralelas (T2-T4 envs; T9-T12 frontend) son grupos
de 3-4.

## Anti-patrones detectados (y evitados)

- ❌ Mezclar T6 (Pydantic) y T9 (frontend payload) en un solo commit:
  romperia atomicidad. T6 cambia el contrato del backend; T9 lo
  satisface desde el frontend. Si T6 va sin T9, el deploy a dev rompe
  todas las apps. **Mitigacion**: T6 NO se deploya hasta T14 (la
  Lambda en dev/stage/prod sigue corriendo el codigo previo hasta el
  redeploy en T14).
- ❌ Lanzar T9-T12 en paralelo sin que T5-T8 esten commiteados:
  podria haber drift de la API contractual. **Mitigacion**: T5-T8 son
  base secuencial; T9-T12 lanza despues.
- ❌ T2-T4 antes que T8: el handler todavia no leeria
  `cloudfront-viewer-country`. **Mitigacion**: T8 base secuencial,
  T2-T4 envs ejecutan en T14 (deploy real), no antes.

---

Siguiente: [06. Commits →](06-commits.md)
