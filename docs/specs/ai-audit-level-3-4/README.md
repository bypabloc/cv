# Plan: ai-audit Level 3-4 (subir score isitagentready de 2/5 a 4/5)

> Plan para subir el score `isitagentready.com` de **2/5 (Bot-Aware)** a
> **4/5 (Agent-Capable)** implementando: (a) fix del archivo
> `.well-known/api-catalog` que hoy cae en el SPA fallback de Cloudflare
> Pages, (b) Markdown estatico (`.md` duplicado por pagina) compatible con
> Free tier, (c) MCP Server (Model Context Protocol) con 2-3 tools de
> consulta del CV + server card en `/.well-known/mcp/server-card.json`.

## Estado por fase

| Fase | Descripcion | Estado | Commits |
|------|-------------|--------|---------|
| 0 | Diagnostico bug SPA fallback en `/.well-known/api-catalog` | Pendiente | 1 |
| 1A | Fix api-catalog: renombrar a `.json` + redirect 200 | Pendiente | 1 |
| 1B | Markdown estatico: prebuild genera `.md` duplicado por pagina | Pendiente | 2 |
| 1C | Cloudflare Transform Rule: `Accept: text/markdown` → `.md` | Pendiente | 1 |
| 2A | MCP Server endpoint via Cloudflare Pages Functions | Pendiente | 2 |
| 2B | MCP tools: `get_cv_section`, `list_projects`, `search_experience` | Pendiente | 2 |
| 2C | MCP Server Card en `/.well-known/mcp/server-card.json` | Pendiente | 1 |
| 3 | Validar skills + rules con `claude -p` | Pendiente | 1 |
| 4 | Verificacion E2E + ai_audit + PR a dev | Pendiente | 1 |

**Total estimado**: 12 commits, ~15-20 archivos modificados, ~6-12h de trabajo.

## Tabla "Cuando leer"

| Capitulo | Cuando leer |
|----------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Antes de empezar — contexto del problema, decision tomada, criterios de aceptacion (AC-1 a AC-12) |
| [02-fase-0-diagnostico.md](02-fase-0-diagnostico.md) | Antes de implementar Fase 1A — reproduccion del bug del SPA fallback |
| [03-fase-1a-fix-api-catalog.md](03-fase-1a-fix-api-catalog.md) | Implementar fix del api-catalog (renombrar + redirect 200) |
| [04-fase-1b-markdown-estatico.md](04-fase-1b-markdown-estatico.md) | Implementar prebuild que genera `.md` duplicado por cada pagina HTML |
| [05-fase-1c-cloudflare-transform-rule.md](05-fase-1c-cloudflare-transform-rule.md) | Configurar Transform Rule en dashboard de Cloudflare |
| [06-fase-2a-mcp-server-endpoint.md](06-fase-2a-mcp-server-endpoint.md) | Implementar endpoint MCP en Cloudflare Pages Functions |
| [07-fase-2b-mcp-tools.md](07-fase-2b-mcp-tools.md) | Implementar las 3 tools del MCP server |
| [08-fase-2c-mcp-server-card.md](08-fase-2c-mcp-server-card.md) | Publicar server card en `/.well-known/mcp/server-card.json` |
| [09-fase-3-validar-skills.md](09-fase-3-validar-skills.md) | Validacion de skills/rules con `claude -p` (matriz 5 prompts) |
| [10-commits.md](10-commits.md) | Listado completo de commits con mensajes en Conventional Commits |
| [11-paralelizacion-worktrees.md](11-paralelizacion-worktrees.md) | Que fases se pueden paralelizar con git worktrees |
| [12-verificacion-e2e.md](12-verificacion-e2e.md) | Bateria final de comandos + criterio de cierre + PR |

## Decisiones no-reabribles

1. **Plan Cloudflare = Free** → NO usar feature managed "Markdown for Agents"
   (requiere Pro $20/mes). Pivote a alternativa estatica: prebuild genera
   `.md` duplicado por cada pagina HTML + Cloudflare Transform Rule
   redirige `Accept: text/markdown` al `.md`.

2. **NO implementar OAuth/OIDC discovery ni OAuth Protected Resource**
   (`/.well-known/openid-configuration`, `/.well-known/oauth-protected-resource`).
   El portfolio NO tiene auth real. Publicar stubs es anti-pattern y
   confunde a los agentes. Joost.blog (83/100 = Level 5) deliberadamente
   rechaza estos checks por la misma razon. Aceptar la penalizacion
   intencional de isitagentready es correcto.

3. **MCP server vive en Cloudflare Pages Functions** (NO en el Lambda AWS
   del backend). Razones: (a) Free tier de Pages Functions = 100k
   req/dia, (b) co-locado con el sitio, (c) MCP usa JSON-RPC distinto al
   patron `operation+action` de los Lambdas, (d) cada Pages project sirve
   sus propias Functions automaticamente sin coordinacion con el
   provisioner serverless de devtools.

4. **6 MCP servers (uno por niche), tools identicos** — isitagentready
   audita cada subdominio independientemente. Si solo el apex tiene MCP,
   los 5 niches restantes seguiran reportando "MCP Server Card not
   found". Compartir el codigo via paquete `@portfolio/mcp` (nuevo) +
   thin wrapper por niche en `apps/*/functions/mcp.ts`.

5. **3 tools del MCP server, NO mas en este plan**: `get_cv_section`,
   `list_projects`, `search_experience`. Suficiente para pasar el check
   de isitagentready y para uso real de agentes. Mas tools = scope creep,
   se agrega despues si hay demanda.

6. **Rama base: `feature/ai-audit-level-3-4` desde `dev`** (no desde
   `feature/lambdas-async-sqs` que estaba activa cuando se creo este
   plan). Un solo PR `feature/ai-audit-level-3-4 -> dev`. Las
   promociones a stage/prod son posteriores al merge y siguen el flujo
   normal.

## Reglas criticas

- **SIEMPRE** Free tier compatible (no requiere upgrade Cloudflare Pro).
- **SIEMPRE** los builders nuevos viven en `packages/seo/src/lib/` y
  se invocan desde `apps/*/scripts/build-public-assets.mjs` (mismo
  patron que `buildHeaders`/`buildRedirects`/`buildApiCatalog`).
- **SIEMPRE** las MCP tools comparten codigo via paquete (nuevo)
  `packages/mcp`. NUNCA duplicar handlers en 6 apps.
- **SIEMPRE** asserts EXACTOS en tests (`expect(x).toBe(42)`, NUNCA
  `toBeGreaterThan(0)`). Coverage >= 80% per-file.
- **SIEMPRE** Conventional Commits en espanol, sin atribucion IA.
- **NUNCA** breaking changes en builders existentes (`buildHeaders`,
  `buildApiCatalog`, etc.). Solo agregar.
- **NUNCA** declarar el plan completo sin que `ai_audit` contra prod
  muestre score >= 75 (objetivo 80+) y `isitagentready` >= 3/5 en al
  menos 3 niches.

## Matriz de verificacion

| Cambio | Verificacion local | Verificacion post-deploy |
|--------|-------------------|--------------------------|
| Fix api-catalog | `pnpm run build` + grep el dist + `curl -I` local con preview | `curl -s https://the-full-stack.com/.well-known/api-catalog \| jq .` debe devolver JSON parseable |
| Markdown estatico | unit tests del builder + 1 .md generado por pagina | `curl -H "Accept: text/markdown" https://the-full-stack.com/about` retorna `.md` |
| MCP endpoint | unit tests + `wrangler pages dev` local | `curl -X POST https://the-full-stack.com/mcp -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'` retorna tools |
| MCP server card | grep dist | `curl -s https://the-full-stack.com/.well-known/mcp/server-card.json` JSON valido |
| Cierre | `pnpm test` + `pnpm build` + `ai_audit` local contra dev | `ai_audit` contra prod muestra score >= 75 |

## Resultado esperado

| Tool | Baseline (2026-05-25T23:47) | Objetivo post-plan |
|------|----------------------------|--------------------|
| isitagentready | 2/5 (40) | **3-4/5** (60-85) |
| lighthouse_psi | 92-100/100 | sin cambio (ya alto) |
| validators | 88/100 | **95-100/100** (api-catalog ahora valido) |
| **Avg global** | **74.83/100** | **>= 85/100** |

## Navegacion

Empezar por [01-contexto-y-decision.md](01-contexto-y-decision.md).
