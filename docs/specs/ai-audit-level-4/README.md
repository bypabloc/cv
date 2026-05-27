---
status: in-progress
created: 2026-05-27
owner: Pablo Contreras
target-branch: feature/ai-audit-level-4
audit-target: https://the-full-stack.com
audit-current: 2/5 isitagentready (post plan ai-audit-level-3-4)
audit-target-score: 3-4/5 isitagentready (ceiling intencional)
---

# Plan ai-audit-level-4 — fix regresion + automatizacion

> Continuacion del plan `ai-audit-level-3-4`. Tras el deploy a prod del
> plan anterior se descubrio que los artefactos clave (Pages Function
> `/mcp` + `.well-known/*.json`) NO funcionan en runtime:
>
> - **`/mcp`**: POST devuelve HTTP 405; el bundle del Worker contiene
>   `import.meta.glob()` (de Vite) y el runtime de Cloudflare Workers
>   no lo implementa -> `TypeError: ...glob is not a function`.
> - **`.well-known/api-catalog.json` y `.well-known/mcp/server-card.json`**:
>   los `_headers` aplican `Content-Type` correcto, pero Cloudflare Pages
>   sirve el `index.html` (SPA fallback) — los archivos NO se uploadean
>   porque `.well-known/` es un dotfile (regla de wrangler).
> - **Transform Rule TR-1** (`Accept: text/markdown` -> `.md`): nunca se
>   activo (era manual en el dashboard, anti-pattern).
> - **`api-catalog.json`** linkset apunta a `api.portfolio.*/openapi.json`
>   que NO existe.
>
> Resultado: el audit re-corrido contra prod (2026-05-27T00:53:34Z) dio
> 2/5 isitagentready en los 6 niches. Igual que antes del plan anterior.

## Cuando leer este plan

| Archivo | Cuando |
|---------|--------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Problema, solucion, AC numerados |
| [02-fase-0-diagnostico.md](02-fase-0-diagnostico.md) | Evidencia de los 4 bugs + analisis raiz |
| [03-fase-1-mcp-bundle-fix.md](03-fase-1-mcp-bundle-fix.md) | Refactor @portfolio/mcp + snapshot JSON inyectado |
| [04-fase-2-wellknown-fix.md](04-fase-2-wellknown-fix.md) | Opciones A->B->C para `.well-known/` |
| [05-fase-3-openapi-static.md](05-fase-3-openapi-static.md) | openapi.json estatico minimo (POST /contact, GET /track) |
| [06-fase-4-mcp-tools-verify.md](06-fase-4-mcp-tools-verify.md) | Validar /mcp + 3 tools end-to-end |
| [07-fase-5-markdown-middleware.md](07-fase-5-markdown-middleware.md) | Pages Function `_middleware.ts` para content negotiation |
| [08-commits.md](08-commits.md) | Listado de commits + Conventional |
| [09-paralelizacion-worktrees.md](09-paralelizacion-worktrees.md) | Fases 3 y 5 paralelas via worktrees |
| [10-verificacion-e2e.md](10-verificacion-e2e.md) | Bateria E2E final + cierre del plan |

## Estado por fase

| Fase | Estado | Bloqueante para |
|------|--------|-----------------|
| Fase 0 — Diagnostico | DONE | Todas |
| Fase 1 — Fix MCP bundle | PENDING | Fase 2A, Fase 4, Fase 5, Fase 6 |
| Fase 2 — Fix `.well-known/` | PENDING | Fase 6 |
| Fase 3 — openapi.json estatico | PENDING (paralelo con 5) | Fase 6 |
| Fase 4 — Verificar MCP tools | PENDING | Fase 6 |
| Fase 5 — Markdown middleware | PENDING (paralelo con 3) | Fase 6 |
| Fase 6 — Verificacion E2E | PENDING | — |

## Decisiones no-reabribles

1. **MCP usa snapshot JSON en build-time, NO `@portfolio/content` runtime.**
   El bundle del Function NO debe arrastrar `import.meta.glob`. El postbuild
   genera `apps/<niche>/functions/_data/cv-snapshot.json` con todo el CV
   serializado; `mcp.ts` lo importa estaticamente.
2. **3 tools del MCP son el alcance final** (`get_cv_section`,
   `list_projects`, `search_experience`). NO se anaden mas.
3. **`openapi.json` minimo** documenta solo `POST /contact` y
   `GET /track`. Sin auth schemes, sin error responses detallados.
4. **Transform Rule TR-1 se reemplaza por Pages Function `_middleware.ts`**.
   NUNCA activacion manual en el dashboard.
5. **Ceiling 3-4/5 intencional** sigue vigente: NO publicar
   `/.well-known/openid-configuration` ni `/.well-known/oauth-protected-resource`.
6. **El bundle de Pages Functions queda en `<app>/functions/`** (raiz del
   proyecto Pages = `<app>/dist`, pero Wrangler resuelve `<dir>/functions/`
   directamente; en este repo `<dir>` es `<app>/dist` y el wrangler-action
   no soporta `--functions-directory` separado, por lo que el bundle DEBE
   ir a `<app>/dist/functions/` con el codigo listo para Workers runtime,
   sin dependencias rotas).

## Reglas criticas

- Cada commit deja el repo verde (lint + typecheck + tests del scope).
- El ultimo commit elimina `docs/specs/ai-audit-level-4/` (`git rm -r`)
  segun el ciclo de vida del plan-format.
- Verificacion incremental: tras cada fase, deploy a dev y curl-check
  contra `*.portfolio.dev.the-full-stack.com`. NUNCA mergear con un fix
  no verificado en dev.
- `git push` + PR solo cuando la bateria de la Fase 6 pase completa
  en verde — nunca con coverage < 80% o tests rojos.

## Matriz de verificacion

| AC | Verificacion |
|----|--------------|
| AC-1: /mcp responde 200 con JSON-RPC valido | `curl POST /mcp` con initialize/tools/list/tools/call |
| AC-2: /.well-known/api-catalog.json responde JSON valido | `curl /.well-known/api-catalog.json \| jq .linkset` |
| AC-3: /.well-known/mcp/server-card.json responde JSON valido | `curl /.well-known/mcp/server-card.json \| jq .protocolVersion` |
| AC-4: /openapi.json responde OpenAPI 3.x spec | `curl /openapi.json \| jq .openapi` |
| AC-5: `Accept: text/markdown` -> sirve .md | `curl -H "Accept: text/markdown" / \| head` |
| AC-6: isitagentready score >= 3/5 en prod | re-correr `python devtools/run.py ai_audit` |
