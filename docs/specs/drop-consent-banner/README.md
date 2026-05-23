# drop-consent-banner

> Eliminar el banner de consentimiento GDPR del portfolio y dejar el tracking
> always-on (estilo Vercel Analytics: sin cookies, anonimo, sin opt-in
> visible). El backend `/track` ya recibe eventos sin asumir consentimiento;
> la barrera vive solo en el frontend (`CookieBanner.astro` +
> `hasTrackingConsent()` en `track-event.ts`). Este plan la remueve completa.

## Cuando leer cada archivo

| Archivo | Contenido | Cuando leer |
|---------|-----------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Secciones 1-3 del plan: problema, solucion propuesta, criterios de aceptacion (AC-1..AC-8) | Antes de cualquier implementacion — define el "que" y el "por que" |
| [02-flujo-y-archivos.md](02-flujo-y-archivos.md) | Secciones 4-7: diagrama de flujo (antes/despues), ER N/A, tests requeridos (TDD + unit + typecheck + E2E), archivos afectados con comando de verificacion por archivo | Al codear cada cambio |
| [03-descomposicion.md](03-descomposicion.md) | Seccion 8: descomposicion en 7 tareas atomicas con File Exclusivity + Interface Stability + Bounded Scope | Antes de paralelizar |
| [04-commits.md](04-commits.md) | Seccion 9: lista de 10 commits con mensaje Conventional Commits en espanol + verificacion incremental + AC cubierto | Al ejecutar cada commit |
| [05-paralelizacion-worktrees.md](05-paralelizacion-worktrees.md) | Seccion 10: base secuencial + tabla de fases worktree-safe + comandos de lanzamiento | Antes de abrir worktrees |
| [06-verificacion-e2e.md](06-verificacion-e2e.md) | Seccion 11: Parte A (refactor de tests, barrido `rg`) + Parte B (bateria E2E completa) — gate del PR | Antes del ultimo commit + del push |
| [07-definition-of-done.md](07-definition-of-done.md) | Seccion 12: checklist Pre-implementacion + Definition of Done | Antes de marcar el plan como cerrado |

## Estado del plan

| Fase | Archivos | Estado | Verify |
|------|----------|--------|--------|
| 0. Plan | `docs/specs/drop-consent-banner/*` | escrito, no ejecutado | N/A |
| 1. T2 — track-event always-on | `packages/ui/src/lib/track-event.ts` + tests | pending | `pnpm --filter @portfolio/ui exec vitest run track-event` |
| 2. T3a — TrackingPixel limpio | `packages/ui/src/components/TrackingPixel.astro` | pending | `pnpm exec astro check` |
| 3. T3b — Footer sin manage-consent | `packages/ui/src/components/Footer.astro` | pending | `pnpm exec astro check` |
| 4. T4 — Layout + paginas hub | `packages/app-shared/src/layouts/SitePageLayout.astro`, 3 paginas `apps/hub/src/pages/` | pending | `pnpm --filter @portfolio/hub run build` |
| 5. T1 — Borrar artefactos | `CookieBanner.astro`, `cookie-consent.ts`, `cookie-consent.test.ts` | pending | `pnpm exec tsc --noEmit` + `rg -l "cookie-consent\|CookieBanner"` |
| 6. T5 — i18n + schema | `elements.{es,en}.yaml`, `schemas.ts`, `build-strings.test.ts` | pending | `pnpm --filter @portfolio/content run typecheck` |
| 7. T7 — Unit tests restantes | `track-event.test.ts`, `scroll-depth.test.ts`, `click-tracking.test.ts` | pending | `pnpm --filter @portfolio/ui exec vitest run` |
| 8. T6 — E2E specs | `tests/feature/tracking/consent.spec.ts` (borrar), `track-pageload.spec.ts`, `contact-funnel.spec.ts`, `contact-session-link.spec.ts` | pending | `python3 devtools/run.py test_runner --module=feature --type=feature --env=local` |
| 9. Verificacion E2E | bateria completa seccion 11 | pending | Ver [06-verificacion-e2e.md](06-verificacion-e2e.md) |
| 10. Limpieza plan | `git rm -r docs/specs/drop-consent-banner/` | pending | `git status` limpio |

## Decisiones no-reabribles

Resueltas con el usuario antes de escribir el plan. No reabrir sin razon
nueva.

- **D1** Eliminar `CookieBanner.astro` + `cookie-consent.ts` completos. NO se
  conserva una libreria "por si acaso" — el codigo viejo se reescatara de
  git si alguna vez se necesita.
- **D2** Simplificar `track-event.ts`: `trackEvent` queda como
  `sendBeacon(buildPayload(...))` sin gating. Se borran las constantes
  `STORAGE_CONSENT`, `QA_FLAG`, `QA_FLAG_VALUE` y las funciones
  `hasTrackingConsent` / `isTrackingForced`.
- **D3** Eliminar el bypass `?cf_track=force` (QA). Ya no aporta porque el
  default emite siempre. Los 3 E2E specs que lo usan se simplifican.
- **D4** Eliminar el boton "Gestionar consentimiento" del Footer
  (`data-testid="manage-consent"`) + el `<script>` que despacha
  `REOPEN_BANNER_EVENT`. Sin banner no hay nada que gestionar.
- **D5** Eliminar las claves YAML `cookieBanner` (es/en) y
  `footer.manageConsent` (es/en) + el bloque `cookieBanner` del schema Zod
  (`ComponentsStrings`) en `schemas.ts`.
- **D6** Eliminar en `TrackingPixel.astro` el listener
  `portfolio:consent-changed` (lineas 99-102). `page_load` se emite siempre
  en el cold start.
- **D7** Privacy stance documentado en el body del PR (no PII, no cookies,
  session_id en localStorage por 60 dias, backend respeta TTL). NO se agrega
  un nuevo banner / nota en la UI.
- **D8** Solo frontend. El Lambda `tracking_pixel` y el backend de Neon
  quedan intactos en este plan.

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** ejecutar cada commit con su verificacion incremental antes de
  pasar al siguiente (no diferir verificaciones al final).
- **SIEMPRE** el commit 6 (borrar `CookieBanner.astro` + `cookie-consent.ts`)
  va DESPUES de los commits 2-5 — borrar antes rompe imports.
- **SIEMPRE** el commit 10 incluye `git rm -r docs/specs/drop-consent-banner/`
  (carpeta del plan es efimera, ver `.claude/rules/plan-format.md`).
- **NUNCA** dejar referencias residuales: el barrido `rg` de la seccion 11
  Parte A debe dar 0 resultados sobre 10 keywords (`CookieBanner`,
  `cookie-consent`, `cf_consent`, `cf_track`, `REOPEN_BANNER_EVENT`,
  `CONSENT_CHANGED_EVENT`, `hasTrackingConsent`, `isTrackingForced`,
  `cookieBanner`, `manageConsent`).
- **NUNCA** push ni PR con un comando de la bateria E2E fallando o coverage
  < 80% per-file.
- **NUNCA** mergear este plan sin antes promover su PR `feature/* -> dev`
  via merge commit (politica del repo, ver `.claude/rules/git-workflow.md`).

## Matriz de verificacion (resumen)

| Que verificar | Comando | Cuando |
|---------------|---------|--------|
| Lint + format | `pnpm exec biome check .` | cada commit |
| Typecheck TS + Astro | `pnpm exec tsc --noEmit && pnpm exec astro check` | cada commit |
| Unit pkg ui | `pnpm --filter @portfolio/ui exec vitest run` | commits 2, 8 |
| Unit pkg content | `pnpm --filter @portfolio/content exec vitest run` | commit 7 |
| Unit pkg app-shared | `pnpm --filter @portfolio/app-shared exec vitest run` | commit 8 |
| Build 6 apps | `pnpm run build` | commits 5, 10 |
| Barrido sin keywords | `rg -l '<10 keywords>' -g '!dist' -g '!node_modules' -g '!docs/specs' apps packages tests` | commit 10 (debe dar 0) |
| Playwright E2E | `python3 devtools/run.py test_runner --module=feature --type=feature --env=local` | commit 10 |

## Rama de trabajo

`feature/drop-consent-banner` (parte de `dev`). PR `feature/drop-consent-banner
-> dev` con merge commit (NO `--delete-branch=false`: `feature/*` se borra
al mergear; `dev` es permanente).

## Navegacion

- Inicio aqui (README)
- Siguiente: [01-contexto-y-decision.md](01-contexto-y-decision.md)
- Reglas del formato: [.claude/rules/plan-format.md](../../../.claude/rules/plan-format.md)
- Reglas de la carpeta del plan (efimera): [.claude/docs/plan-format-large/README.md](../../../.claude/docs/plan-format-large/README.md)
