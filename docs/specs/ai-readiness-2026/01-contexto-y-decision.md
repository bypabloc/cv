# 01 — Contexto, solucion y criterios de aceptacion

## 1. Contexto / Problema

### Estado real medido (22-May-2026, scan en isitagentready.com)

El portfolio `the-full-stack.com` esta en **33/100 — Level 2 Bot-Aware**.
Cumple lo basico de SEO/GEO clasico (robots.txt, sitemap, JSON-LD,
content signals, allowlist de 10 AI bots) pero le faltan **todos los
estandares 2025-2026** que las IAs en runtime usan para descubrir
APIs y ejecutar acciones:

| Categoria | Score actual | Detalle |
|-----------|--------------|---------|
| Discoverability | 8/12 (67%) | Falta Link headers (RFC 8288) |
| Content | 0/4 (0%) | Sin Markdown negotiation |
| Bot Access Control | 8/8 (100%) | OK — robots.txt + Content Signals |
| API/Auth/MCP/Skill | 0/24 (0%) | **6 items en cero** |
| Commerce | N/A | No aplica (portfolio no vende) |

### Items concretos en cero (los 6 que rompen el score)

1. **API Catalog** — `/.well-known/api-catalog` debe retornar
   `application/linkset+json` con la lista de APIs publicas (RFC 9727)
2. **MCP Server Card** — `/.well-known/mcp/server-card.json` (SEP-2127)
3. **Agent Skills index** — `/.well-known/agent-skills/index.json`
4. **WebMCP** — `navigator.modelContext.provideContext()` en runtime
5. **Markdown Negotiation** — `Accept: text/markdown` debe retornar
   markdown (Cloudflare AutoRAG pattern)
6. **Link headers** — homepage debe enviar header `Link: ...; rel="..."`

Items intencionalmente excluidos:

- OAuth/OIDC discovery — el portfolio no tiene APIs autenticadas
- Web Bot Auth — request signing, requiere infra extra; defer
- x402 / ACP / MPP / UCP — commerce, no aplica

### Trigger del plan

El usuario investigo (sessions previas) que estos estandares existen.
Confirmado con scan real, los items son verificables/medibles. La meta
es subir de **33 a 70+** ejecutando solo lo que el scan mide.

### Hallazgos de exploracion

- El portfolio tiene **6 apps Astro** en `apps/{generic,hub,fintech,architect,leader,vibe}/`
  cada una con su `public/robots.txt` y `public/llms.txt` ya armados por
  `apps/<app>/scripts/build-public-assets.mjs` (prebuild script).
- Existe el package `@portfolio/seo` (`packages/seo/src/lib/`) con
  builders ya usados: `buildLlmsTxt`, `buildRobotsTxt`,
  `buildSitemap`, `buildPersonSchema`, `buildProfilePageSchema`,
  `buildSiteNavigationSchema`. Aqui se agregan los nuevos builders.
- El backend serverless tiene la Lambda `cv` (lectura del CV desde Neon
  via GET /cv?operation=cv&action=<entity>) ya deployada. NO se modifica.
- La Lambda `nlweb` nueva se crea como hermana en
  `serverless/lambda/services/nlweb/` siguiendo el patron `lambda-controller`
  (`manifest.yaml`, `pyproject.toml`, `core/{handler,controllers,services,models,settings}/`).
  Reusa `shared.db` (Neon engine cacheado) y `shared.cache` (`@cached(ttl=300)`).
- WebMCP es API W3C en estado **Working Draft** (Chrome incubation,
  webmachinelearning.github.io), expuesta como `navigator.modelContext`.
  Firefox/Safari no la soportan aun — implementar con feature-detect.

## 2. Solucion propuesta

Implementar los **6 items faltantes** en 5 fases atomicas, cada una
con su verificacion incremental. La arquitectura sigue tres capas:

```text
+----------------------------------------------------------+
|  Capa 1 — Static well-known (Astro endpoints)            |
|  apps/<app>/src/pages/.well-known/*.ts                   |
|  - api-catalog.json.ts                                   |
|  - mcp/server-card.json.ts                               |
|  - agent-skills/index.json.ts                            |
|  Generados via @portfolio/seo nuevos builders            |
+----------------------------------------------------------+
                          |
                          | (los endpoints apuntan a)
                          v
+----------------------------------------------------------+
|  Capa 2 — Runtime hints (frontend JS en homepage)        |
|  apps/<app>/src/components/WebMCPRegistration.astro      |
|  - navigator.modelContext.provideContext({tools: [...]}) |
|  - feature-detect: typeof navigator.modelContext         |
|  - tools coinciden con MCP Server Card                   |
+----------------------------------------------------------+
                          |
                          | (las tools del WebMCP llaman a)
                          v
+----------------------------------------------------------+
|  Capa 3 — Backend NLWeb (Lambda Python)                  |
|  serverless/lambda/services/nlweb/                       |
|  POST /nlweb/ask {query: string, niche?: string}         |
|  - Retrieval estructurado sobre Neon (cv_experiences,    |
|    cv_projects, cv_skills) con fuzzy match              |
|  - Response: schema.org JSON-LD con entries             |
|  - Cached 5min via shared.cache                         |
+----------------------------------------------------------+
                          |
                          | Adicional (Capa 2.5):
                          v
+----------------------------------------------------------+
|  Markdown content negotiation + Link headers             |
|  apps/<app>/src/middleware.ts (Astro middleware)         |
|  - if Accept: text/markdown -> retorna .md generado     |
|  - Link header en homepage con rel api-catalog,         |
|    service-doc, mcp                                     |
+----------------------------------------------------------+
```

### Decisiones clave

**Decision 1**: Los endpoints `.well-known/*` se generan via **Astro
endpoints** (`src/pages/.well-known/*.ts` con `export const GET = ...`)
y NO via prebuild script a `public/`. Razon: necesitan ser tipados
(Zod schemas) y reusar imports de `@portfolio/content` (lista de
experiences, projects). Si fueran static, duplicariamos data.

**Decision 2**: **Un solo Astro middleware** maneja markdown content
negotiation Y agrega Link headers a la homepage. Vive en
`packages/app-shared/src/middleware.ts` (compartido entre las 6 apps).
Razon: misma logica, no duplicar.

**Decision 3**: La generacion del markdown de cada pagina se hace
**on-the-fly desde el HTML buildeado**, no precomputado. Astro
`output: 'static'` genera HTML; el middleware corre solo en
content-negotiation. Se usa `turndown` para HTML -> Markdown.
Tradeoff: latencia ~30ms vs. tamano de bundle de archivos `.md`
preparados (6 apps x ~20 paginas = 120 archivos). Preferimos
on-the-fly.

**Decision 4**: La Lambda `nlweb` recibe **solo POST** (no GET).
Razon: `Accept: application/schema+json` + body con `{query, niche}`
es el patron de NLWeb oficial. El bot que descubre via MCP Server Card
sabe que tool `ask` espera POST.

**Decision 5**: El scan automatizado se hace via **Playwright headless
contra isitagentready.com**, no via API (no existe). El script vive en
`devtools/agent_readiness_scan/` y publica el output a
`docs/progress/agent_readiness_<timestamp>.json` (gitignored —
artefacto efimero).

**Decision 6**: Las tools que el WebMCP registra en runtime y las
declaradas en `mcp/server-card.json` son **la misma lista**, leida
desde una unica fuente de verdad: `packages/seo/src/data/mcp-tools.ts`.

### Constraints considerados

- **No agregar libs JS pesadas** al bundle del frontend. `turndown` es
  liviano (~10KB gzip) y solo se carga server-side en el middleware.
- **No bloquear CI** con el scan (lento, externo). Scan = manual
  post-deploy.
- **Compatibilidad con Cloudflare Pages** (output static). El
  middleware Astro funciona como Cloudflare Worker en deploy (ya
  configurado). El markdown negotiation pasa por el Worker.

## 3. Criterios de Aceptacion (AC)

Formato BDD numerado. Cada AC mapea a tests en la fase correspondiente.

### Endpoints `.well-known/*`

- **AC-1**: Given un crawler IA hace `GET /.well-known/api-catalog`
  contra cualquiera de las 6 apps, When Astro responde, Then retorna
  HTTP 200 con `Content-Type: application/linkset+json` y body con
  array `linkset` de al menos 2 entries (NLWeb endpoint y CV endpoint).

- **AC-2**: Given un agente MCP hace `GET /.well-known/mcp/server-card.json`,
  When Astro responde, Then retorna HTTP 200 con `Content-Type:
  application/json`, conforme a SEP-2127 (campos `serverInfo`,
  `transport`, `capabilities`), declarando al menos 3 tools:
  `cv.get_experiences`, `cv.get_projects`, `nlweb.ask`.

- **AC-3**: Given un agente hace `GET /.well-known/agent-skills/index.json`,
  When Astro responde, Then retorna `$schema`, array `skills` con al
  menos 4 skills (`search-cv`, `download-cv`, `contact`, `ask-nlweb`),
  cada uno con `name`, `type`, `description`, `url`, `sha256`.

- **AC-4**: Given las 6 apps en deploy, When se corre el scan, Then
  todas reportan los 3 endpoints validos (no soft-404, content-type
  correcto, JSON parseable).

### Content negotiation + Link headers

- **AC-5**: Given un agente hace `GET /` con header
  `Accept: text/markdown`, When Astro middleware responde, Then
  retorna HTTP 200 con `Content-Type: text/markdown; charset=utf-8`
  y body markdown derivado del HTML.

- **AC-6**: Given un browser normal hace `GET /` (default
  `Accept: text/html`), When Astro responde, Then retorna HTML normal
  sin afectar el flujo actual.

- **AC-7**: Given cualquier request a `/`, When Astro responde, Then
  incluye header `Link: </.well-known/api-catalog>; rel="api-catalog",
  </.well-known/mcp/server-card.json>; rel="mcp", </llms.txt>;
  rel="service-doc"`.

### NLWeb Lambda

- **AC-8**: Given un POST a la Lambda nlweb con body
  `{"query": "fintech experience", "niche": "fintech"}`, When la
  Lambda procesa, Then retorna HTTP 200 con
  `Content-Type: application/ld+json`, body conforme a schema.org
  (`@context: "https://schema.org"`, `@type: "ItemList"`) con array
  `itemListElement` de experiencias/proyectos matchados.

- **AC-9**: Given una query NLWeb que no matchea nada en Neon, When la
  Lambda procesa, Then retorna HTTP 200 con `itemListElement: []` y
  campo `numberOfItems: 0` (no 404).

- **AC-10**: Given dos requests identicos a NLWeb dentro de 5min, When
  la Lambda procesa, Then el segundo es servido desde cache
  (`shared.cache @cached(ttl=300)`) — verificable por header
  `X-Cache: HIT` en la respuesta.

### WebMCP runtime

- **AC-11**: Given un browser que soporta WebMCP (Chrome canary 2026
  con flag) abre `the-full-stack.com`, When la pagina termina de
  cargar, Then `navigator.modelContext` esta definido y registra al
  menos 3 tools (mismas del MCP Server Card). Verificable via
  `await navigator.modelContext.listTools()`.

- **AC-12**: Given un browser sin WebMCP (Firefox, Safari, Chrome
  stable sin flag), When la pagina carga, Then la pagina funciona
  identico (no consola error, no UI rota) — feature-detect activo.

### Score objetivo

- **AC-13**: Given el script de scan corrido contra
  `https://stage.the-full-stack.com` post-deploy, When el scan
  termina, Then el score reportado es **>= 70/100**.

- **AC-14**: Given el script de scan corrido contra los 6 subdominios
  en stage, When el scan termina, Then los 6 reportan score >= 70/100
  (un solo subdominio bajo el umbral falla el AC).
