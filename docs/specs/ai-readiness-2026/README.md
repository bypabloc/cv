# Spec ai-readiness-2026 — Subir Cloudflare Agent Readiness Score de 33 a 70+

> Implementar los estandares 2025-2026 que faltan para que IAs (Claude,
> ChatGPT, Cursor, agentes Playwright/MCP) descubran y consuman el
> portfolio en runtime: `agent-manifest.txt`, `.well-known/mcp/server-card.json`,
> `/.well-known/api-catalog`, markdown content negotiation, link headers,
> WebMCP runtime hints y una Lambda NLWeb que conteste preguntas sobre el
> CV desde Neon.
>
> **Score actual** (22 May 2026, scan real): **33/100 — Level 2 Bot-Aware**
> **Score objetivo**: **70+/100 — Level 4 Agent-Ready**

## Estado por fase

| Fase | Archivo | Estado |
|------|---------|--------|
| 0 | [01-contexto-y-decision.md](01-contexto-y-decision.md) | pendiente |
| 1 — well-known endpoints (Astro) | [02-fase-well-known-endpoints.md](02-fase-well-known-endpoints.md) | pendiente |
| 2 — content negotiation + link headers | [03-fase-content-negotiation.md](03-fase-content-negotiation.md) | pendiente |
| 3 — NLWeb Lambda | [04-fase-nlweb-lambda.md](04-fase-nlweb-lambda.md) | pendiente |
| 4 — WebMCP runtime (navigator.modelContext) | [05-fase-webmcp-runtime.md](05-fase-webmcp-runtime.md) | pendiente |
| 5 — devtools scan script | [06-fase-scan-devtools.md](06-fase-scan-devtools.md) | pendiente |
| — | [07-archivos-afectados.md](07-archivos-afectados.md) | pendiente |
| — | [08-commits.md](08-commits.md) | pendiente |
| — | [09-paralelizacion-worktrees.md](09-paralelizacion-worktrees.md) | pendiente |
| — | [10-verificacion-e2e.md](10-verificacion-e2e.md) | pendiente |

## Decisiones (NO reabribles)

Estas decisiones se cerraron via `AskUserQuestion` antes de escribir el
plan. No se renegocian en la fase de implementacion.

1. **Scope de apps**: los `.well-known/*` endpoints se publican en **las
   6 apps Astro** (generic, hub, fintech, architect, leader, vibe). Cada
   subdominio expone su propio set de metadata referido a su niche.
   Razon: cada subdominio es un sitio independiente desde la perspectiva
   de un crawler/agente; la IA llega a cualquiera de ellos por busqueda
   o link directo y debe encontrar el manifest local.

2. **NLWeb = Lambda nueva separada** (`serverless/lambda/services/nlweb/`),
   no extension de la Lambda `cv`. Razon: NLWeb es un protocolo con
   contrato propio (`POST /ask`, `Accept: application/schema+json`) que
   no encaja en el patron action-based de `cv`. Manifest, pyproject y
   ciclo de deploy independientes. Reusa `shared.db` y `shared.cache` —
   ambas ya estan en `serverless/lambda/shared/`.

3. **Sin LLM en NLWeb — retrieval estructurado**. El endpoint hace
   busqueda fuzzy/keyword sobre Neon (tablas `cv_experiences`,
   `cv_projects`, `cv_skills`) y retorna entries que matchean en JSON
   schema.org. La IA cliente (Claude/ChatGPT) razona sobre el resultado.
   Costo $0, latencia <200ms (warm), reusa el `@cached` de la libreria
   `shared.cache`.

4. **Scan via scraping headless, no API**. isitagentready.com NO expone
   API publica documentada. Implementar `devtools/run.py
   agent_readiness_scan` que usa Playwright (ya esta como devdep) para
   abrir la web, ingresar la URL, esperar el resultado y parsear el
   score + breakdown. Output JSON para CI/historial.

5. **Numeracion de items del scan = guia de prioridad**. El scan real
   del 22-May-2026 mostro 6 items en cero en "API/MCP". Esos definen el
   contenido tecnico de las fases — no se inventan endpoints abstractos,
   se implementan exactamente los que el scanner busca:

   | Item del scan | Donde lo cubre el plan |
   |---------------|------------------------|
   | API Catalog (`/.well-known/api-catalog`) | Fase 1 |
   | MCP Server Card (`/.well-known/mcp/server-card.json`) | Fase 1 |
   | Agent Skills index (`/.well-known/agent-skills/index.json`) | Fase 1 |
   | Markdown Negotiation (`Accept: text/markdown`) | Fase 2 |
   | Link headers (RFC 8288) | Fase 2 |
   | WebMCP (`navigator.modelContext`) | Fase 4 |
   | OAuth/OIDC discovery | NO se implementa (no aplica, sin auth) |
   | Web Bot Auth signatures | NO se implementa (defer Fase 7 si sube en prioridad) |

6. **Rama**: `feature/ai-readiness-2026` desde `dev`. Un solo PR a `dev`.
   Promocion `dev -> stage -> main` via PRs separados (ver
   `.claude/rules/git-workflow.md`).

## Reglas criticas (siempre activas durante la implementacion)

- **SIEMPRE** los endpoints Astro de `.well-known/` retornan
  `Content-Type: application/json` (o `application/linkset+json` para
  api-catalog). El scan marca soft-404 si reciben HTML.
- **SIEMPRE** el manifest del Lambda `nlweb` declara
  `SSM_NEON_URL_PATH=/portfolio/{stage}/neon-url` — NUNCA hardcodear la
  URL ni leerla de env plano.
- **SIEMPRE** los responses del Lambda nlweb son schema.org JSON-LD
  valido (`@context: https://schema.org`).
- **SIEMPRE** que se agreguen tools al MCP server card y al WebMCP
  runtime, deben coincidir (mismas tools en ambos lados — desync rompe
  agentes que descubren via .well-known y ejecutan via WebMCP).
- **NUNCA** mockear el scan de Cloudflare en CI (lentitud + flakiness).
  El scan corre manual post-deploy a stage. CI valida solo que los
  endpoints retornan JSON valido.
- **NUNCA** publicar la URL real de `api.portfolio.the-full-stack.com` en
  el `mcp.json` de `dev` (cada stage referencia el suyo:
  `api.portfolio.dev`, `api.portfolio.stage`, `api.portfolio`).

## Matriz de verificacion (resumen — detalle en fase 10)

| Verificacion | Cuando | Comando |
|--------------|--------|---------|
| JSON valido en endpoints | cada commit que toca `pages/.well-known/` | `pnpm exec vitest run packages/seo` |
| Schema.org valido en NLWeb | cada commit en `services/nlweb/` | `serverless tests --type=unit --lambda=nlweb` |
| Markdown content-negotiation | post-build | `curl -H 'Accept: text/markdown' http://localhost:9970/` |
| WebMCP tools registrados | E2E Playwright | tests/feature en `feature/ai-readiness/` |
| Score >= 70 | post-deploy a stage | `python devtools/run.py agent_readiness_scan --url=https://stage.the-full-stack.com` |
| Score por subdominio | post-deploy a stage | scan corrido para los 6 subdominios |

## Estimacion

| Fase | Esfuerzo | Worktree-safe |
|------|----------|---------------|
| 1 — well-known endpoints | 3-4h | si (despues de base) |
| 2 — content negotiation + link headers | 2h | si |
| 3 — NLWeb Lambda | 4-5h | si (paquete aislado) |
| 4 — WebMCP runtime | 2h | si |
| 5 — devtools scan | 2h | si |
| 6 — verificacion E2E | 2h | NO (sequential, ultima fase) |
| **Total** | **15-17h** | — |

> El usuario pidio "2-3 horas" original. El scan real subio el alcance:
> 6 items faltantes en API/MCP + necesidad de markdown + link headers +
> WebMCP runtime. Las "2-3h" cubren SOLO la Fase 1 + 5 (well-known
> estaticos + scan). Las fases 2-4 son las que llevan el score a 70+.

## Como leer el plan

1. **Empezar por** [01-contexto-y-decision.md](01-contexto-y-decision.md):
   problema, solucion, criterios de aceptacion (AC-1 a AC-12).
2. **Implementar fase por fase** (02 -> 05). La fase 04 (WebMCP) depende
   de tener las URLs del Lambda nlweb publicadas, asi que va despues de
   la fase 03.
3. **Cierre** con [10-verificacion-e2e.md](10-verificacion-e2e.md): el
   bucle "scan real -> ajustar -> re-scan" se itera hasta llegar a 70+.
4. La carpeta `docs/specs/ai-readiness-2026/` se elimina en el ultimo
   commit del plan (artefacto efimero — ver
   `.claude/rules/plan-format.md`).
