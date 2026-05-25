# 09 — Paralelizacion con git worktrees

> Desde que commit se puede paralelizar y que fases son worktree-safe.

## Base secuencial obligatoria

Commits **1, 2, 3 y 4** se hacen en orden en la rama principal
(`feature/ai-readiness-2026`) ANTES de lanzar worktrees. Razon:

- Commit 1 crea la carpeta del plan (referencia para todos).
- Commit 2 crea `packages/seo/src/data/{mcp-tools,api-base}.ts` que
  importa toda la Fase 1 y Fase 4 (WebMCP).
- Commit 3 toca `shared/lambda_kit/http_dispatch.py`, que es prerequisito
  del Lambda nlweb (Fase 3). Si no se hace antes, las 4 fases lo
  necesitan.
- Commit 4 crea los 3 builders en `@portfolio/seo` que los endpoints
  Astro importan. Sin esto, los commits 5-9 fallarian en build.

Tras commit 4, **se puede paralelizar**.

## Fases worktree-safe (paralelizables tras commit 4)

| Worktree | Fase | Branch | Archivos disjuntos | Lleva commits |
|----------|------|--------|--------------------|--------------:|
| **wt-1** | Fase 1 — endpoints en 6 apps | `feature/ai-readiness-2026-wt-endpoints` | `apps/{generic,hub,fintech,architect,leader,vibe}/src/pages/.well-known/**` | 5-9 |
| **wt-2** | Fase 2 — middleware + adapter | `feature/ai-readiness-2026-wt-middleware` | `packages/app-shared/src/middleware/**`, `packages/app-shared/tests/unit/middleware/**`, las 6 `astro.config.ts`, las 6 `src/middleware.ts`, los 6 `package.json` de app | 10-11 |
| **wt-3** | Fase 3 — Lambda nlweb | `feature/ai-readiness-2026-wt-nlweb` | `serverless/lambda/services/nlweb/**` (carpeta entera nueva) | 12-17 |
| **wt-4** | Fase 5 — devtools scan | `feature/ai-readiness-2026-wt-devtools` | `devtools/agent_readiness_scan/**`, `devtools/tests/agent_readiness_scan/**`, `devtools/pyproject.toml` | 20 |

**4 worktrees concurrentes**, todos disjuntos a nivel archivo.

> Las fases 4 (WebMCP runtime) y 6 (verificacion E2E final) **NO** son
> worktree-safe. Ver "Lo que NO se paraleliza" abajo.

## Verificacion de file exclusivity (los 3 checks)

| Worktree | File Exclusivity | Interface Stability | Bounded Scope |
|----------|------------------|---------------------|---------------|
| wt-1 (endpoints) | ✓ Solo `apps/*/src/pages/.well-known/` | ✓ Importa builders ya commiteados (commit 4) | ✓ 3 endpoints x 6 apps = 18 archivos |
| wt-2 (middleware) | ✓ Solo `packages/app-shared/src/middleware/` y configs de apps. NO toca `pages/` ni `BaseLayout` | ✓ Solo agrega un `onRequest` export, no rompe nada existente | ✓ Acotado al middleware |
| wt-3 (nlweb) | ✓ Solo `serverless/lambda/services/nlweb/` (carpeta nueva) | ✓ Reusa `shared.lambda_kit` ya commiteado (commit 3) | ✓ Lambda autocontenida |
| wt-4 (devtools) | ✓ Solo `devtools/agent_readiness_scan/` y `devtools/pyproject.toml` (append-only) | ✓ Nuevo plugin, no toca run.py | ✓ Script autocontenido |

## Tabla de colisiones potenciales

| Recurso | wt-1 | wt-2 | wt-3 | wt-4 |
|---------|------|------|------|------|
| `apps/*/src/pages/` | ESCRIBE | — | — | — |
| `apps/*/src/middleware.ts` | — | ESCRIBE | — | — |
| `apps/*/src/layouts/BaseLayout.astro` | — | — | — | — |
| `apps/*/astro.config.ts` | — | ESCRIBE | — | — |
| `apps/*/package.json` | — | ESCRIBE | — | — |
| `packages/seo/` | LEE | LEE | LEE | — |
| `packages/app-shared/src/middleware/` | — | ESCRIBE | — | — |
| `packages/app-shared/src/components/` | — | — | — | — |
| `serverless/lambda/services/nlweb/` | — | — | ESCRIBE | — |
| `serverless/lambda/shared/` | — | — | LEE | — |
| `devtools/agent_readiness_scan/` | — | — | — | ESCRIBE |
| `devtools/pyproject.toml` | — | — | — | ESCRIBE |

Cero colisiones. Los 4 worktrees pueden trabajar en paralelo.

## Lo que NO se paraleliza

### Fase 4 — WebMCPRegistration en BaseLayout

Los commits 18 y 19 tocan archivos que TAMBIEN tocaria wt-2 si lo
extendieramos a "todo lo de apps shared". Para mantener atomicidad:

- Commit 18 (`feat(app-shared): WebMCPRegistration`) toca
  `packages/app-shared/src/components/` y `index.ts`. wt-2 toca
  `packages/app-shared/src/middleware/` y `index.ts`. **Colision en
  `index.ts`** (`export {} ...` se appende). Mitigacion: merge de wt-2
  primero, despues commit 18 en la rama principal (post-merge).

- Commit 19 toca `apps/*/src/layouts/BaseLayout.astro`. wt-2 no toca
  layouts. Aqui no hay colision tecnica, pero el commit 19 necesita
  que `WebMCPRegistration` este exportado desde `@portfolio/app-shared`
  (commit 18). Asi que **commits 18 y 19 van en la rama principal post
  merge de wt-1, wt-2 y wt-3**.

### Fase 6 — Verificacion E2E final (commit 21)

Es la ultima fase del plan, secuencial. Corre la bateria completa
(`docs/specs/ai-readiness-2026/10-verificacion-e2e.md`) y solo cuando
todo pasa, se commitea el `git rm -r docs/specs/ai-readiness-2026/`.

## Orden de merge a la rama principal

```text
feature/ai-readiness-2026 (commits 1-4 ya hechos)
       │
       ├──── wt-1 (endpoints)  ──── merge ────┐
       ├──── wt-2 (middleware) ──── merge ────┤
       ├──── wt-3 (nlweb)      ──── merge ────┤
       ├──── wt-4 (devtools)   ──── merge ────┤
       │                                       v
       │                            feature/ai-readiness-2026
       │                            (post-merge de los 4 worktrees)
       │
       ├──── commit 18 (WebMCPRegistration en app-shared)
       ├──── commit 19 (BaseLayout x6)
       ├──── commit 20 (devtools scan ya commiteado en wt-4 - skip)
       │
       └──── commit 21 (verificacion E2E + rm -r plan)
                 ↓
             PR: feature/ai-readiness-2026 -> dev
```

Cada merge de worktree -> rama principal usa `git merge --no-ff` para
preservar el contexto del worktree en el grafo (opcional, mejora
trazabilidad).

## Como lanzar cada worktree

```bash
# Desde la rama principal (feature/ai-readiness-2026) tras commit 4:

# wt-1 — endpoints
git worktree add ../portfolio-wt-endpoints feature/ai-readiness-2026-wt-endpoints
cd ../portfolio-wt-endpoints
# Trabajar commits 5-9 aqui

# wt-2 — middleware
git worktree add ../portfolio-wt-middleware feature/ai-readiness-2026-wt-middleware
cd ../portfolio-wt-middleware
# Trabajar commits 10-11 aqui

# wt-3 — nlweb
git worktree add ../portfolio-wt-nlweb feature/ai-readiness-2026-wt-nlweb
cd ../portfolio-wt-nlweb
# Trabajar commits 12-17 aqui

# wt-4 — devtools
git worktree add ../portfolio-wt-devtools feature/ai-readiness-2026-wt-devtools
cd ../portfolio-wt-devtools
# Trabajar commit 20 aqui
```

Cada worktree es una copia independiente del repo, con su propia rama y
su propio `node_modules` (re-instalar con `pnpm install` por worktree).
El share del git filesystem reduce el costo de disco.

### Limpieza de worktrees

Una vez todos mergeados a `feature/ai-readiness-2026`:

```bash
git worktree remove ../portfolio-wt-endpoints
git worktree remove ../portfolio-wt-middleware
git worktree remove ../portfolio-wt-nlweb
git worktree remove ../portfolio-wt-devtools
git branch -d feature/ai-readiness-2026-wt-{endpoints,middleware,nlweb,devtools}
```

## Concurrencia maxima

**4 agentes/subagentes concurrentes** (uno por worktree). Dentro del
limite de 5-7 recomendado en `.claude/rules/plan-format.md`.

## Anti-patrones

- ❌ Lanzar wt-3 (nlweb) ANTES del commit 3 (`http_dispatch` POST):
  fallarian los tests del Lambda porque `extract_request_post` no
  existe.
- ❌ Lanzar wt-1 (endpoints) ANTES del commit 4 (los 3 builders):
  fallarian los imports en los endpoints Astro.
- ❌ Mergear wt-2 DESPUES de los commits 18-19: colision en
  `packages/app-shared/src/index.ts`.
- ❌ Lanzar la Fase 4 (WebMCPRegistration) como worktree separado: la
  base secuencial necesaria es muy especifica (post-merge de los otros
  3 worktrees + lectura de `index.ts` actualizado).
- ❌ Lanzar la Fase 6 como worktree: la verificacion E2E necesita
  TODOS los commits, no se puede hacer en paralelo.
