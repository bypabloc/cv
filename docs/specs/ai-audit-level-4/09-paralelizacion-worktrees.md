# Paralelizacion con git worktrees

## Base secuencial (obligatoria — NO paralelizable)

Commits 1, 2 y 3 van en la rama principal `feature/ai-audit-level-4`:

1. **Plan inicial** (carpeta del plan).
2. **Fase 1** — MCP bundle fix. Tocan `packages/mcp/*`, `packages/markdown-export/*`,
   `apps/*/functions/mcp.ts`, `apps/*/scripts/postbuild-*.mjs`.
   Cambia los contracts de `@portfolio/mcp` (interface `MCPDataProvider`).
3. **Fase 2A** — `.well-known/*` Functions. Tocan
   `apps/*/functions/.well-known/*`, `packages/seo/src/lib/build-{headers,redirects}.ts`,
   `apps/*/scripts/build-public-assets.mjs`.

## Fases worktree-safe

Tras commit 3 (Fase 2A) en `feature/ai-audit-level-4`, las fases 3 y 5
pueden ejecutarse en paralelo via git worktrees:

| Worktree | Branch | Toca |
|----------|--------|------|
| `tmp/wt-openapi` | `feature/ai-audit-level-4-openapi` | `packages/seo/src/lib/build-openapi.ts`, `packages/seo/src/lib/build-api-catalog.ts`, `packages/seo/tests/unit/*`, `apps/*/scripts/build-public-assets.mjs` |
| `tmp/wt-middleware` | `feature/ai-audit-level-4-middleware` | `packages/markdown-export/src/lib/build-middleware.ts`, `apps/*/functions/_middleware.ts`, `cloudflare/transform-rules.md` (eliminar) |

### Crear worktrees

```bash
# Desde feature/ai-audit-level-4 con commit 3 ya hecho
git worktree add tmp/wt-openapi -b feature/ai-audit-level-4-openapi
git worktree add tmp/wt-middleware -b feature/ai-audit-level-4-middleware
```

### Lanzar agentes en paralelo

- Worktree `openapi` -> ejecuta `05-fase-3-openapi-static.md`
- Worktree `middleware` -> ejecuta `07-fase-5-markdown-middleware.md`

Ambos commiten en su rama. Al terminar:

```bash
# Volver a la rama principal
cd /home/bypabloc/projects/bypabloc/portfolio

# Mergear los 2 worktrees (merge commit)
git merge feature/ai-audit-level-4-openapi --no-edit
git merge feature/ai-audit-level-4-middleware --no-edit

# Limpiar
git worktree remove tmp/wt-openapi
git worktree remove tmp/wt-middleware
git branch -d feature/ai-audit-level-4-openapi feature/ai-audit-level-4-middleware
```

## Colisiones detectadas

- `apps/<niche>/scripts/build-public-assets.mjs`: tocado por Fase 2A y
  Fase 3. Por eso Fase 3 va DESPUES de Fase 2A en la base secuencial.
- `apps/<niche>/functions/` (dir): tocado por Fase 1 (mcp.ts), Fase 2A
  (.well-known/*) y Fase 5 (_middleware.ts). Como son archivos
  distintos, hay file-exclusivity dentro del dir.
- `packages/markdown-export/src/lib/`: Fase 1 (bundle-pages-function.ts
  con loader json) y Fase 5 (build-middleware.ts) son archivos
  distintos, OK.

## Lo que NO se paraleliza

- Verificacion incremental en dev (deploy + curl-check). Es un recurso
  compartido (`apps/<niche>/dist/` se sobreescribe en cada deploy y el
  workflow `deploy-apps.yml` corre matrix 6 niches secuencial por niche).
  Es posible deployar tras cada commit, pero la validacion E2E final
  (Fase 6) se hace una sola vez con TODO mergeado.
- Fase 6 (verificacion final). Es la ultima fase, secuencial obligatoria.

## Decision para este plan

**Lineal en la rama principal** salvo que Fase 1 y Fase 2A se completen
sin problemas. Si Fase 2A toma >2 horas (por iteracion A->B->C),
paralelizar Fases 3 y 5 con worktrees mientras se resuelve Fase 2.

Si Fase 2 colapsa al investigacion exhaustiva, Fases 3 y 5 pueden
deployarse sin Fase 2 (los AC-4 y AC-5 son independientes de AC-2/AC-3).
