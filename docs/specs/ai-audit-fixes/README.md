# Plan: ai-audit-fixes

> Implementar los fixes accionables detectados por `ai_audit` en
> prod (run `2026-05-25T22-13-22`): subir el promedio del audit
> de 63/100 a ~85+/100. Los cambios viven en `packages/seo` +
> `packages/ui` + `devtools/ai_audit/` (compartido), NO se
> duplica en `apps/*/public/`.
>
> Rama: `feature/ai-audit-devtools` (continuamos en la misma).

## Arquitectura compartida (descubrimiento)

Los archivos publicos identicos en las 6 apps (`_headers`,
`robots.txt`, `llms.txt`) NO se editan a mano: los **genera
`packages/seo`** en runtime de build a traves de
`apps/<X>/scripts/build-public-assets.mjs` (prebuild hook).

Por lo tanto, todos los fixes que serian "6 archivos identicos"
se vuelven UN cambio en `packages/seo` + reflejarlo en los 6
prebuild scripts (que solo llaman a las funciones).

| Concern | Antes (mi instinto) | Despues (arquitectura real) |
|---|---|---|
| Link headers | 6 archivos `_headers` | `packages/seo/lib/build-headers.ts` |
| /sitemap.xml alias | 6 archivos `_redirects` | nuevo `packages/seo/lib/build-redirects.ts` |
| /.well-known/api-catalog | 6 archivos identicos | nuevo `packages/seo/lib/build-api-catalog.ts` |
| WebSite JSON-LD | 6 layouts | `packages/seo/lib/build-website-schema.ts` + 1 cambio en `packages/app-shared` |
| Color contrast tokens | (ya era) | `packages/ui/src/styles/tokens.css` |
| Validator devtools | (ya era) | `devtools/ai_audit/validators.py` + `tools/validators.py` |

## Estado por fase

| # | Fase | Archivos a tocar | Estado |
|---|------|------------------|--------|
| 0 | [Contexto + decisiones](01-contexto-y-decision.md) | docs only | pendiente |
| 1 | [packages/seo: 3 builders nuevos](02-fase-packages-seo.md) | `packages/seo/src/lib/*` + tests | pendiente |
| 2 | [packages/ui: color contrast tokens](03-fase-packages-ui-tokens.md) | `packages/ui/src/styles/tokens.css` | pendiente |
| 3 | [devtools: validator robots + sitemap fallback](04-fase-devtools-validator.md) | `devtools/ai_audit/validators.py` + tests | pendiente |
| 4 | [apps: actualizar 6 prebuild scripts](05-fase-prebuild-scripts.md) | `apps/*/scripts/build-public-assets.mjs` (6) | pendiente |
| 5 | [packages/app-shared: WebSite JSON-LD en layout](06-fase-app-shared-jsonld.md) | `packages/app-shared/src/*` | pendiente |
| 6 | [Validar skills con claude -p](07-fase-validar-skills.md) | (verifica `.claude/*`) | pendiente |
| 7 | [Commits secuencia](08-commits.md) | (doc del plan) | pendiente |
| 8 | [Paralelizacion worktrees](09-paralelizacion-worktrees.md) | (doc del plan) | pendiente |
| 9 | [Verificacion E2E + PR + cierre](10-verificacion-e2e.md) | re-run audit + push + PR a dev + eliminar carpeta | pendiente |

## Decisiones no-reabribles

1. **Cloudflare "Content Signals" managed robots.txt** se queda activado.
   - Razon: el sitio gana certificacion de respeto a content signals.
   - Trade-off: validators detecta AI bots bloqueados (estado correcto
     desde la perspectiva del owner — los bots SI estan bloqueados).
   - Accion: actualizamos el validator para tratar este caso como
     `neutral` (no `fail`) cuando detecta el bloque managed.

2. **Markdown content negotiation (`Accept: text/markdown`)** se DEFIERE.
   - Razon: requiere Cloudflare Worker. Subir de level 2 a 3 en
     isitagentready no compensa mantener un Worker por ahora.

3. **OAuth metadata** queda como N/A.
   - Razon: el portfolio NO tiene flow OAuth. Documentado en docs/ai-audit
     que estos checks son esperados como fail.

4. **API Catalog `.well-known/api-catalog`** SE IMPLEMENTA.
   - Razon: el portfolio tiene API serverless publica (POST /track,
     /contact). Exponer el catalog la hace "agent-discoverable".

5. **Color contrast fix** — subir `--color-text-muted` y
   `--color-text-subtle` 1 paso de la escala greys.
   - Cambio visual minimo, ganancia WCAG AA garantizada.

6. **TODO archivo compartido vive en packages/seo o packages/ui**.
   - NUNCA duplicar 6 veces en `apps/*/public/`. Si una pieza no
     puede vivir en packages, justificar caso por caso.

## Reglas criticas (heredadas del proyecto)

- Conventional commits en espanol (ver `git-workflow.md`).
- NUNCA atribucion de IA en commits.
- Cada fase deja repo verde (lint + typecheck + tests + build).
- El ultimo commit del plan (`10-verificacion-e2e.md`) incluye
  `git rm -r docs/specs/ai-audit-fixes/`.
- Push + PR SOLO con la bateria de la fase 9 en verde.

## Matriz de verificacion

| Capa | Comando |
|------|---------|
| Lint TS | `pnpm exec biome check .` |
| Typecheck TS | `pnpm exec tsc --noEmit && pnpm exec astro check` |
| Tests packages | `pnpm exec vitest run` |
| Tests devtools | `python devtools/run.py test_runner --module=devtools --type=unit` |
| Build estatico | `pnpm run build` (los 6 sites) |
| Audit final | `python devtools/run.py ai_audit` (comparar contra baseline) |
| Skills | `claude -p` (ver fase 6) |

## Audit baseline (antes del plan)

```text
Run: 2026-05-25T22-13-22
Average: 63/100

isitagentready : 2/5 (Bot-Aware)
  ├─ discoverability     67%
  ├─ contentAccessibility 0%
  ├─ botAccessControl   100%
  ├─ discovery            0%
  └─ commerce            n/a

validators     : 50/100
  ├─ llms.txt           100  OK
  ├─ robots.txt           0  FAIL (managed, intencional)
  ├─ sitemap.xml          0  FAIL (sitio sirve sitemap-index.xml)
  └─ json-ld            100  OK

lighthouse_psi : 99/100 (hub: 100/100)
  ├─ performance        100
  ├─ seo                100
  ├─ accessibility       97  FAIL (color-contrast)
  └─ best-practices     100
```

## Audit objetivo (despues del plan)

```text
Average esperado: ~85/100

isitagentready : 2/5  (stays — Markdown content negotiation requiere
                       Worker; los fixes mejoran 'discovery' de 0 a ~30%
                       pero el level requiere mas)
validators     : 100/100  (sitemap detectable + robots tratado como neutral)
lighthouse_psi : 100/100  (color contrast fix)
```
