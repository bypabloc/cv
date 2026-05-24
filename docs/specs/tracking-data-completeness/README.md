# Plan: tracking-data-completeness

> Completar la captura del pageview del portfolio: el frontend deja de mandar
> 9 campos que la tabla `tracking_events` necesita (page_*, utm_*, viewport_*,
> devicePixelRatio), el Lambda pasa a resolver `country` desde el header
> `cloudfront-viewer-country` (custom domains migrados a Edge-Optimized en los
> 3 envs), el regex custom del UA se reemplaza por `ua-parser` oficial y se
> droppea la columna legacy `stream_event_id`. Adicionalmente se habilita
> view transitions de Astro (ClientRouter) en las 6 apps y el tracking
> dispara en `astro:page-load` para cubrir hard navigation + client-side nav.

## Estado del plan

| Fase | Archivo | Estado |
|------|---------|--------|
| 0. Indice + decisiones | [README.md](README.md) | redactado |
| 1. Contexto y decision (secciones 1-3) | [01-contexto-y-decision.md](01-contexto-y-decision.md) | redactado |
| 2. Diagramas (secciones 4-5) | [02-diagramas-flujo-er.md](02-diagramas-flujo-er.md) | redactado |
| 3. Tests requeridos (seccion 6) | [03-tests-requeridos.md](03-tests-requeridos.md) | redactado |
| 4. Archivos afectados (seccion 7) | [04-archivos-afectados.md](04-archivos-afectados.md) | redactado |
| 5. Descomposicion (seccion 8) | [05-descomposicion-paralelizacion.md](05-descomposicion-paralelizacion.md) | redactado |
| 6. Commits (seccion 9) | [06-commits.md](06-commits.md) | redactado |
| 7. Worktrees (seccion 10) | [07-paralelizacion-worktrees.md](07-paralelizacion-worktrees.md) | redactado |
| 8. Verificacion E2E (seccion 11) | [08-verificacion-e2e.md](08-verificacion-e2e.md) | redactado |
| 9. Validacion + DoD (seccion 12) | [09-validacion-done.md](09-validacion-done.md) | redactado |
| 10. View transitions design (referencia) | [10-view-transitions-design.md](10-view-transitions-design.md) | redactado |
| 11. Navbar dropdown fix (referencia) | [11-navbar-dropdown-fix.md](11-navbar-dropdown-fix.md) | redactado |

Sin ejecutar todavia. Branch: `feature/tracking-data-completeness` (desde
`dev`). El plan se elimina con `git rm -r` en el ultimo commit (regla
[plan-format.md](../../../.claude/rules/plan-format.md)).

## Cuando leer cada capitulo

| Necesito saber... | Leer |
|-------------------|------|
| Por que existe este plan y que entrega | [01](01-contexto-y-decision.md) |
| Antes/despues del flujo y ER de la tabla | [02](02-diagramas-flujo-er.md) |
| Que tests escribir y a que AC mapean | [03](03-tests-requeridos.md) |
| Lista de archivos a tocar + comando de verificacion | [04](04-archivos-afectados.md) |
| Como descomponer en tareas atomicas | [05](05-descomposicion-paralelizacion.md) |
| Secuencia exacta de los 14 commits | [06](06-commits.md) |
| Donde paralelizar con git worktrees | [07](07-paralelizacion-worktrees.md) |
| Bateria final de verificacion antes del PR | [08](08-verificacion-e2e.md) |
| Checklist DoD para cerrar el plan | [09](09-validacion-done.md) |

## Decisiones no-reabribles (acordadas con el usuario)

1. **PK de `tracking_events`**: se mantiene la actual
   `(session_id, page_id, created_at)` (la tabla esta particionada por
   `created_at`; PG exige la partition key en la PK). Solo se droppea
   `stream_event_id`.
2. **Campos obligatorios en el payload**: `page_path`, `page_url`,
   `page_title`, `viewport_width`, `viewport_height`, `utm_source`,
   `utm_medium`, `utm_campaign`, `utm_content`. Default `''` en el front
   cuando no aplica (no hay query string utm, etc). `referrer` queda
   best-effort (string vacio si no hay).
3. **Country**: recrear los 3 custom domains (`api.portfolio.dev`,
   `api.portfolio.stage`, `api.portfolio`) como **Edge-Optimized**.
   `cloudfront-viewer-country` llegara solo. NO se agrega CloudFront
   distribution propia ni se usa GeoIP.
4. **UA parser**: reemplazar el regex custom (`shared/observability/`)
   por `ua-parser` (uap-python). Vendoring selectivo via uv.
5. **Migration de datos**: truncate `tracking_events` en dev Y prod en
   commit 13. No hay backfill.
6. **View transitions**: habilitar `<ClientRouter />` de Astro en
   `BaseLayout` de las 6 apps. El tracking dispara en
   `astro:page-load` (cubre hard navigation + SPA). Guard contra doble
   disparo en la primera carga.
7. **Granularidad**: 14 commits, plan Large.
8. **No cron GeoLite2**: el fallback geo no se implementa en este plan.

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** la branch del plan es `feature/tracking-data-completeness`
  (desde `dev`). Ningun cambio se hace directamente en `dev`/`stage`/`main`.
- **SIEMPRE** el commit 1 es la carpeta del plan; commit 14 incluye la
  bateria de verificacion E2E + `git rm -r docs/specs/tracking-data-completeness/`.
- **SIEMPRE** cada commit ejecuta su verificacion incremental ANTES de
  commitear (lint + typecheck + tests del scope tocado).
- **SIEMPRE** los nuevos campos required del payload entran como
  string vacio por default en el front (NO se rompe la API cuando no hay
  utm o cuando `document.referrer` esta vacio).
- **SIEMPRE** la migracion del custom domain a Edge-Optimized se hace en
  ventana con DNS TTL bajo previo (ver [04](04-archivos-afectados.md) y
  [08](08-verificacion-e2e.md)).
- **NUNCA** `git push` ni PR antes de que la bateria E2E final (capitulo
  [08](08-verificacion-e2e.md)) pase completa en verde.
- **NUNCA** truncate sobre prod sin el flag `confirm: true` en el event
  Lambda (la operacion vive en `events/truncate-tracking.json` con guard).
- **NUNCA** atribucion de IA en commits ni en el PR body.

## Matriz de verificacion (resumen)

| Comando | Cuando | Donde |
|---------|--------|-------|
| `pnpm exec biome check .` | Antes de cada commit | Workspace root |
| `pnpm exec tsc --noEmit && pnpm exec astro check` | Tras tocar TS/Astro | Workspace root |
| `pnpm exec vitest run --coverage` | Tras tocar packages/* | Per-package |
| `python devtools/run.py serverless tests --type=unit --lambda=tracking_pixel` | Tras tocar el Lambda | Lambda root |
| `python devtools/run.py serverless tests --type=coverage --shared` | Tras tocar `shared/*` | Repo root |
| `python devtools/run.py test_runner --module=feature --type=feature --env=local` | Antes del PR | Repo root |
| `curl POST /track ... \| jq` + Neon `SELECT *` | Tras deploy dev | Manual (capitulo 8) |

## Riesgos identificados

| Riesgo | Mitigacion |
|--------|------------|
| Edge-Optimized recrear corta trafico 30s-2min | Bajar DNS TTL a 60s ≥10min antes; ventana fuera de hora pico |
| `ua-parser` agrega ~5-8MB al zip | Vendoring selectivo con uv; validar zip final ≤50MB |
| View transitions cambia comportamiento visual | Playwright valida hard navigation + SPA antes del PR |
| Truncate prod (perdida de datos historicos) | Confirmado por el usuario (datos test, sin valor analitico) |
| Doble disparo tracking en primera carga | Guard `let firstLoad = true` + condicion en handler |

## Referencias cruzadas

- Regla de planificacion: [plan-format.md](../../../.claude/rules/plan-format.md)
- Regla de ejecucion (gate de push/PR): seccion "Regla de ejecucion"
- Lambda controller: [.claude/rules/lambda-controller.md](../../../.claude/rules/lambda-controller.md)
- Neon management: [.claude/rules/neon-management.md](../../../.claude/rules/neon-management.md)
- Secrets server: [.claude/rules/serverless-secrets.md](../../../.claude/rules/serverless-secrets.md)
- CI/CD: [.claude/rules/ci-cd-pipeline.md](../../../.claude/rules/ci-cd-pipeline.md)
