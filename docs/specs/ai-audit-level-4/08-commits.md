# Commits del plan

> Listado de commits incrementales que implementan las 6 fases. Cada
> commit deja el repo verde (lint + typecheck + tests del scope) y es
> revisable. Conventional Commits en espanol, sin atribucion a IA.

## Secuencia

1. **docs(specs): plan ai-audit-level-4 (carpeta inicial)**
   - Crea `docs/specs/ai-audit-level-4/` con README + 10 archivos del plan.
   - Sin cambios de codigo.

2. **feat(mcp): snapshot JSON inyectado en Pages Function** (Fase 1)
   - Refactor `@portfolio/mcp`: handlers reciben `MCPDataProvider`.
   - Nuevo `snapshot-provider.ts` + tests.
   - Postbuild `postbuild-mcp-snapshot.mjs` genera
     `functions/_data/cv-snapshot.json` en cada niche.
   - `apps/<niche>/functions/mcp.ts` (x6) usa el snapshot estatico.
   - Verificacion: `grep import.meta.glob dist/functions/mcp.js` -> 0
     hits + `wrangler pages dev` local responde JSON-RPC valido.
   - AC: AC-1.

3. **feat(seo,functions): sirve .well-known/*.json via Pages Functions** (Fase 2A)
   - Crea `apps/<niche>/functions/.well-known/api-catalog.json.ts` y
     `apps/<niche>/functions/.well-known/mcp/server-card.json.ts`.
   - Postbuild genera JSON snapshots en `_data/`.
   - Elimina la generacion de los `.well-known/*.json` como assets +
     entradas de `_headers`/`_redirects`.
   - Verificacion: deploy a dev + curl-check del JSON valido.
   - AC: AC-2, AC-3.
   - Si la opcion A FALLA en dev: commits 3b (Opcion B) o 3c (Opcion C).

4. **feat(seo): openapi.json estatico minimo (POST /contact, GET /track)** (Fase 3)
   - Nuevo builder `build-openapi.ts` + tests.
   - Cada app escribe `dist/openapi.json` en prebuild.
   - `build-api-catalog.ts` apunta linkset a `{host}/openapi.json`.
   - AC: AC-4.

5. **feat(functions): middleware Accept: text/markdown -> .md (reemplaza Transform Rule)** (Fase 5)
   - Nuevo `_middleware.ts` por niche (codegen via
     `build-middleware.ts` en `@portfolio/markdown-export`).
   - Elimina `cloudflare/transform-rules.md`.
   - AC: AC-5.

6. **chore(specs): cierra plan ai-audit-level-4 (verificacion E2E completa)** (Fase 6)
   - `git rm -r docs/specs/ai-audit-level-4/`.
   - Documenta en el body del commit:
     - Resultados de la bateria de la Fase 6 (lint, typecheck, tests,
       coverage, build, E2E).
     - Resultado del audit re-corrido contra prod (AC-6).
     - Issues remanentes si los hay.

## Reglas por commit

- ANTES de hacer `git add`: ejecutar la verificacion incremental
  declarada en el archivo de la fase correspondiente.
- Si la verificacion falla -> corregir -> re-verificar -> commitear.
- NO mezclar fases en un mismo commit.
- `git push` y crear el PR SOLO cuando la Fase 6 entera pase verde.

## Resumen de secuencia + paralelizacion

```text
1. plan inicial (carpeta)
2. Fase 1: MCP bundle fix             [BLOQUEANTE]
   |
   +---+--------------------+
   |   |                    |
3. Fase 2 (A->B->C)        |
   |                        |
4. Fase 3 (openapi)        5. Fase 5 (middleware)  [paralelizable]
   |                        |
   +------------------------+
                |
6. Fase 6 (verificacion E2E + cierre)
                |
              push + PR -> dev
```

Commits 4 y 5 son worktree-safe (no tocan los mismos archivos). Ver
`09-paralelizacion-worktrees.md` para el detalle.
