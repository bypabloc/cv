# 01 — Contexto, Solucion, Criterios de Aceptacion

## 1. Contexto / Problema

El plan `ai-audit-level-3-4` (mergeado en `feature/ai-audit-level-3-4` ->
`dev` -> `stage` -> `main` el 2026-05-27) prometia subir
isitagentready de 2/5 a ~4/5. El re-audit contra prod
(`tmp/ai-audit/2026-05-27T00-53-34/`) dio 2/5 igual.

Diagnostico (Fase 0 detallada en `02-fase-0-diagnostico.md`):

1. **Pages Function `/mcp` rota**: POST devuelve HTTP 405 (worker no
   arranca). Causa: el bundle de esbuild incluye `import.meta.glob`
   (Vite-only) heredado de `@portfolio/content -> i18n/index.ts`.
   El runtime de Cloudflare Workers no implementa `import.meta.glob`
   y lanza `TypeError: (intermediate value).glob is not a function`.
   `wrangler pages dev dist` local reproduce el bug.

2. **`.well-known/*.json` sirven HTML del SPA fallback**: los `_headers`
   declaran `Content-Type: application/linkset+json` o
   `application/json`, pero el cuerpo es el `index.html` del Astro
   build. Causa: Cloudflare Pages **excluye dotfiles/dotdirs del
   upload por defecto** (`.well-known/` empieza con `.`). El archivo
   `dist/.well-known/api-catalog.json` existe localmente pero no se
   uploadea, por lo que la URL cae al SPA fallback que respeta el
   `Content-Type` del `_headers` -> mime correcto + cuerpo HTML.

3. **Transform Rule TR-1 nunca activada**: el plan documento
   activacion manual en el dashboard. Anti-pattern: no es
   versionable, no es CI-friendly, queda olvidado.

4. **`openapi.json` apuntado por el linkset NO existe**: el JSON
   actual de `/.well-known/api-catalog.json` linkea a
   `https://api.portfolio.the-full-stack.com/openapi.json` que
   devuelve 404 — el backend no lo expone.

5. **Issues de discoverability**: isitagentready hoy reporta 5 fixes
   para los 6 niches (en orden de severidad):
   - `[high][contentAccessibility]` Support Accept: text/markdown
   - `[medium][discovery]` API Catalog is not valid JSON
   - `[medium][discovery]` /.well-known/mcp/server-card.json invalid JSON
   - `[medium][discovery]` No OAuth/OIDC discovery (ceiling intencional)
   - `[medium][discovery]` No OAuth Protected Resource (ceiling intencional)

## 2. Solucion Propuesta

Plan en 6 fases (0..5) + Fase 6 de verificacion E2E:

### Fase 1 — Fix MCP bundle (snapshot JSON inyectado)

Refactor de `@portfolio/mcp`:

- Los 3 handlers de tools (`get_cv_section`, `list_projects`,
  `search_experience`) reciben los datos del CV como parametro
  inyectado en runtime, NO importan de `@portfolio/content` directo.
- `handleRequest(body, dataProvider)` acepta una funcion factory de datos.
- Cada `apps/<niche>/functions/mcp.ts` pasa un `dataProvider` que
  importa un JSON snapshot pre-buildeado en
  `apps/<niche>/functions/_data/cv-snapshot.json`.
- Nuevo postbuild `postbuild-mcp-snapshot.mjs` genera el snapshot leyendo
  `@portfolio/content` desde Node (con vite-node, donde
  `import.meta.glob` SI funciona) y serializandolo a JSON.
- El bundle de la Function ya no arrastra `@portfolio/content`; solo
  `@portfolio/mcp` (puro TS, sin Vite) + JSON estatico.

Resultado: el bundle ya no tiene `import.meta.glob`, Workers runtime lo
ejecuta sin error.

### Fase 2 — Fix `.well-known/` (3 opciones secuenciales)

**Opcion A — Servir via Pages Functions** (primera en probar):

- Crear `apps/<niche>/functions/.well-known/api-catalog.json.ts` y
  `apps/<niche>/functions/.well-known/mcp/server-card.json.ts`.
- Cada Function lee un JSON snapshot generado por el postbuild
  (`apps/<niche>/functions/_data/api-catalog.json` y
  `apps/<niche>/functions/_data/mcp-server-card.json`) y lo devuelve
  con el `Content-Type` correcto.
- Bypasea el bug del dotfile upload porque las Functions NO son assets.
- Coste: 6 niches × 2 Functions = 12 Functions adicionales. Free tier
  Pages: 100k req/dia (sobrado, audit corre 1-2 veces/semana).
- Eliminar archivos `.well-known/*.json` del output de
  `build-public-assets.mjs` (ya no son assets).

**Opcion B — `wrangler.toml` con `[assets]`** (si A falla):

- Crear `apps/<niche>/wrangler.toml` con
  `[assets] directory = "./dist"` + bind a la regla de inclusion de
  dotfiles. Investigar version actual de wrangler 4.x para sintaxis
  exacta.
- Modificar `deploy-apps.yml` para pasar `--config wrangler.toml`.

**Opcion C — `.assetsignore` con `!.well-known/**`** (si B falla):

- Crear `apps/<niche>/dist/.assetsignore` con `!.well-known/**` (sintaxis
  de gitignore-style inversa para incluir).
- El archivo se genera en build (no commiteado).

**Si A, B y C fallan**: investigacion exhaustiva en web sobre el stack
(Cloudflare Pages Free, wrangler 4, Astro 6) y reformular en un fase
nueva.

### Fase 3 — `openapi.json` estatico (paralelo con Fase 5)

- Crear `packages/seo/src/lib/build-openapi.ts` que genera el OpenAPI
  3.1 spec con 2 paths:
  - `POST /contact` (body: form + Turnstile token; responses: 202, 400, 429)
  - `GET /track` (query params; response: 200 image/gif)
- Prebuild de cada app escribe `dist/openapi.json` desde el builder.
- Actualizar `build-api-catalog.ts` para linkear a
  `https://{host}/openapi.json` en vez de
  `https://api.portfolio.the-full-stack.com/openapi.json`.

### Fase 4 — Verificar MCP tools end-to-end

- Tests E2E del Function vivo en dev:
  - `curl POST /mcp` con `initialize` -> protocolVersion 2025-11-25
  - `tools/list` -> 3 tools con nombres correctos
  - `tools/call name=get_cv_section args=section=about` -> Markdown
    con el about del CV
  - `tools/call name=list_projects` -> array de proyectos
  - `tools/call name=search_experience args=keyword=fintech` -> matches
- Si pasa: 3 tools confirmados como alcance final, NO se agregan mas.

### Fase 5 — Markdown middleware (paralelo con Fase 3)

- Crear `apps/<niche>/functions/_middleware.ts` que intercepte requests
  con `Accept: text/markdown` y reescriba la URL interna a
  `/<path>/index.md` (o `/<path>.md` segun naming actual del postbuild
  de markdown-export).
- Si la URL no tiene `.md` correspondiente -> pasar al asset por
  defecto.
- Reemplaza Transform Rule TR-1 (manual). Eliminar
  `cloudflare/transform-rules.md` que documenta el approach manual.

### Fase 6 — Verificacion E2E

- Bateria local: lint + typecheck + unit + build + (E2E si aplica).
- Deploy a dev. curl-check de los 7 artefactos en
  `https://generic.portfolio.dev.the-full-stack.com` (representativo
  para los 6 niches).
- Promote dev -> stage -> main.
- Re-correr `python devtools/run.py ai_audit` contra prod.
- Confirmar isitagentready >= 3/5 en los 6 niches.
- Commit final: limpieza de la carpeta `docs/specs/ai-audit-level-4/`
  (`git rm -r`).

## 3. Criterios de Aceptacion (AC)

Numerados, BDD-style. Fuente de verdad para tests y verificaciones.

- **AC-1**: Given el deploy en dev, When hago
  `POST https://generic.portfolio.dev.the-full-stack.com/mcp` con body
  `{"jsonrpc":"2.0","id":1,"method":"initialize",...}`,
  Then la respuesta es HTTP 200 + JSON-RPC valido con
  `result.protocolVersion == "2025-11-25"`.

- **AC-2**: Given el deploy en dev, When hago
  `GET /.well-known/api-catalog.json`,
  Then HTTP 200 + Content-Type `application/linkset+json` + el cuerpo
  parsea con `JSON.parse()` sin lanzar y tiene `.linkset[0].anchor`.

- **AC-3**: Given el deploy en dev, When hago
  `GET /.well-known/mcp/server-card.json`,
  Then HTTP 200 + Content-Type `application/json` + el cuerpo parsea
  como JSON y tiene `.protocolVersion == "2025-11-25"` + 3 tools en
  `.tools`.

- **AC-4**: Given el deploy en dev, When hago
  `GET /openapi.json`,
  Then HTTP 200 + Content-Type `application/json` + el cuerpo es
  OpenAPI 3.1 valido con `.paths."/contact".post` y `.paths."/track".get`.

- **AC-5**: Given el deploy en dev, When hago
  `curl -H "Accept: text/markdown" /`,
  Then HTTP 200 + Content-Type `text/markdown` + el cuerpo empieza con
  el contenido del CV en Markdown (NO el HTML del home).

- **AC-6**: Given el deploy en prod tras el plan, When corro
  `python devtools/run.py ai_audit`,
  Then los 6 niches obtienen isitagentready score >= 3/5 (subida real
  de 2/5 a >=3/5). El ceiling 4/5 es el target ideal.

## 4. Diagrama de Flujo

N/A — los cambios no alteran flujos de control del visitante. Solo
afectan que recursos sirve Cloudflare Pages a los crawlers/agentes.

## 5. Diagrama ER

N/A — no hay cambios en base de datos.
