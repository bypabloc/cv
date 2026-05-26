# 01 — Contexto, solucion y criterios de aceptacion

> **Anterior**: [README.md](README.md) · **Siguiente**: [02-fase-0-diagnostico.md](02-fase-0-diagnostico.md)

## 1. Contexto

El audit `python devtools/run.py ai_audit` ejecutado el 2026-05-25T23:47
(post-merge del PR #141 con los ai-audit-fixes) devolvio:

- 18/18 OK, **avg global 74.83/100**
- `isitagentready: 2/5` en los 6 niches (sin cambio vs baseline)
- `lighthouse_psi: 92-100/100`
- `validators: 88/100` (categorias internas: llms.txt=100, robots.txt=50
  neutral, sitemap=100, json-ld=100)

El check `isitagentready` reporta 5 fixes pendientes:

1. [HIGH, reach=8] "Support Accept: text/markdown content negotiation
   for machine-readable content"
2. [MEDIUM, reach=4] "API Catalog is not valid JSON"
3. [MEDIUM, reach=4] "No OAuth/OIDC discovery metadata found"
4. [MEDIUM, reach=4] "No OAuth Protected Resource Metadata found"
5. [MEDIUM, reach=4] "MCP Server Card not found"

### Hallazgos de exploracion

- **El archivo `.well-known/api-catalog` (245 bytes JSON valido) SI esta
  en `apps/*/dist/.well-known/`** y se sube al deploy de Cloudflare
  Pages. Sin embargo:
  - `curl -I` devuelve `HTTP 200 content-type: application/json` ✓
  - `curl` (GET) devuelve el `index.html` del SPA fallback (`content-length:
    83433`, body `<!DOCTYPE html>...`) — con header `content-type:
    application/json` (porque el `_headers` lo aplica por path).
  - El bug es: **Cloudflare Pages aplica SPA fallback (devuelve index.html)
    para rutas sin extension de archivo**. `api-catalog` sin extension cae
    en este comportamiento aunque exista el archivo en el bucket.
- Investigacion via researcher (ver
  `docs/progress/explore_isitagentready-level-3-4.md`):
  - Joost.blog implemento "agent-ready" estatico llegando a **83/100
    (Level 5)** con solo: fix api-catalog + markdown estatico + MCP server
    minimo + rechazo deliberado de OAuth checks.
  - "Markdown for Agents" (managed by Cloudflare) requiere Pro plan
    ($20/mes). El portfolio esta en Free → pivotar a alternativa estatica.

## 2. Solucion Propuesta

Implementar en `feature/ai-audit-level-3-4` (rama desde `dev`) en 9 fases:

### Decisiones clave

**Decision 1**: Renombrar `/.well-known/api-catalog` → `/.well-known/api-catalog.json`
+ agregar redirect 200 (no 301) en `_redirects`, asi ambas URLs sirven el
mismo archivo JSON. Razon: el bug del SPA fallback de Cloudflare Pages
ataca rutas sin extension; con `.json` el archivo se reconoce como
estatico y se sirve directo. El redirect 200 mantiene compatibilidad
con clientes que usan la URL canonica RFC 9727 `/.well-known/api-catalog`.

**Decision 2**: Generar `.md` duplicado por cada pagina HTML en prebuild,
servir via Cloudflare Transform Rule que matchea `Accept: text/markdown`
y reescribe la URL a `.md`. Razon: Free tier compatible, sin Worker, sin
costo recurrente. Trade-off: dist crece ~30% (cada HTML tiene un .md
gemelo). Se mitiga con el conversor estandar de HTML → Markdown (turndown
o equivalente).

**Decision 3**: MCP server vive en **Cloudflare Pages Functions** (uno
por niche, codigo compartido via paquete `@portfolio/mcp` nuevo). NO en
el Lambda AWS. Razon: Free tier 100k req/dia, co-locacion con el sitio,
sin coordinacion con devtools serverless provisioner, MCP usa JSON-RPC
que es ortogonal al patron `operation+action` de los Lambdas.

**Decision 4**: 3 tools del MCP server, ni una mas en este plan:
- `get_cv_section(section: 'about' | 'experience' | 'projects' | 'skills' | 'education' | 'contact')` → devuelve el contenido en Markdown
- `list_projects(tech_stack?: string)` → lista filtrada de proyectos
- `search_experience(keyword: string)` → busca en experiencias laborales

**Decision 5**: NO publicar `/.well-known/openid-configuration` ni
`/.well-known/oauth-protected-resource`. Aceptar la penalizacion
intencional. Documentar la decision en `.claude/rules/ai-audit.md` para
futuras sesiones (regla nueva: "NUNCA stubs OAuth en sitios sin auth").

**Decision 6**: Validar las nuevas skills/rules con `claude -p` siguiendo
`.claude/rules/claude-config-testing.md` (matriz de 5 prompts), antes
del PR a dev.

## 3. Criterios de Aceptacion (AC)

Formato BDD (`Given/When/Then`). Cada AC es convertible a test ejecutable
o comando `curl` post-deploy.

### Fase 0 — Diagnostico

- **AC-0**: Given el dist actual de `apps/generic/dist`, When ejecuto
  `curl -s -X GET https://the-full-stack.com/.well-known/api-catalog`,
  Then la respuesta tiene `content-length > 1000` y body que empieza con
  `<!DOCTYPE html>` (reproduce el bug del SPA fallback).

### Fase 1A — Fix api-catalog

- **AC-1**: Given el archivo renombrado a `.well-known/api-catalog.json`
  + redirect 200 en `_redirects`, When un cliente hace
  `curl -s https://the-full-stack.com/.well-known/api-catalog`, Then
  recibe `HTTP 200` con `content-type: application/json` y body JSON
  parseable que contiene `linkset[0].anchor == 'https://the-full-stack.com'`.
- **AC-2**: Given la misma URL pero terminando en `.json`, When un
  cliente hace `curl -s https://the-full-stack.com/.well-known/api-catalog.json`,
  Then recibe el mismo JSON parseable (sin redirect).

### Fase 1B — Markdown estatico

- **AC-3**: Given una pagina HTML servida en `https://the-full-stack.com/`,
  When ejecuto `pnpm run build` en `apps/generic`, Then existe el archivo
  `apps/generic/dist/index.md` con contenido en Markdown derivado del
  HTML rendered (titulos, parrafos, links, listas).
- **AC-4**: Given el builder `buildMarkdownPage(html)`, When recibe un
  string de HTML con `<h1>Pablo</h1><p>Lorem</p>`, Then devuelve un
  string de Markdown que contiene `# Pablo\n\nLorem`.
- **AC-5**: Given las 6 apps con prebuild ejecutado, When listo
  `find apps/*/dist -name '*.md' | wc -l`, Then el numero es >= 6
  (al menos 1 .md por app, idealmente uno por ruta).

### Fase 1C — Transform Rule

- **AC-6**: Given la Transform Rule activa en Cloudflare, When un agente
  hace `curl -H 'Accept: text/markdown' https://the-full-stack.com/about`,
  Then la respuesta tiene `content-type: text/markdown` (o `text/plain`)
  y el body es el contenido en Markdown (no HTML).

### Fase 2A — MCP endpoint

- **AC-7**: Given el endpoint `apps/generic/functions/mcp.ts` deployado,
  When un cliente hace `curl -X POST https://the-full-stack.com/mcp -H
  'Content-Type: application/json' -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{}},"id":1}'`,
  Then recibe `HTTP 200` con respuesta JSON-RPC valida (capabilities +
  serverInfo).

### Fase 2B — MCP tools

- **AC-8**: Given el handler `tools/list`, When un cliente lo invoca,
  Then la respuesta contiene exactamente 3 tools: `get_cv_section`,
  `list_projects`, `search_experience` (orden estable, asserts EXACTOS).
- **AC-9**: Given el handler `tools/call` con `name=get_cv_section`,
  `arguments={section: 'about'}`, When se ejecuta, Then la respuesta
  contiene `content[0].text` con el contenido del seccion About en
  Markdown extraido de `packages/content`.
- **AC-10**: Given el handler `tools/call` con `name=list_projects`,
  `arguments={tech_stack: 'Astro'}`, When se ejecuta, Then la respuesta
  contiene `content[0].text` con un array JSON de proyectos cuyos
  `techStack` incluyen "Astro".

### Fase 2C — Server card

- **AC-11**: Given el archivo `/.well-known/mcp/server-card.json`
  generado por prebuild + servido por Cloudflare Pages, When un agente
  lo descarga, Then es JSON valido que cumple el schema de
  modelcontextprotocol.io con `endpoint: 'https://the-full-stack.com/mcp'`,
  `protocolVersion: '2025-11-25'`, `tools[]` con 3 entradas.

### Fase 4 — Resultado final

- **AC-12**: Given el codigo final mergeado en `prod` (post promocion
  dev→stage→main), When ejecuto `python devtools/run.py ai_audit`, Then:
  - `isitagentready >= 3/5` en al menos 3 de los 6 niches
  - `validators >= 95/100` en los 6 niches (categoria api-catalog ahora
    cuenta como pass, no fail)
  - `avg global >= 85/100`
  - El reporte NO incluye `"API Catalog is not valid JSON"` ni `"MCP
    Server Card not found"` en el top 5 fixes
