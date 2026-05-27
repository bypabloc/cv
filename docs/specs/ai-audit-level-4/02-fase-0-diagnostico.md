# Fase 0 — Diagnostico consolidado

> Evidencia de los 4 bugs descubiertos tras el deploy del plan
> `ai-audit-level-3-4` a prod. Esta fase NO requiere commit — es
> documentacion del trabajo de Fase 0 ya hecho.

## Bug 1: Pages Function `/mcp` rota

### Sintomas

```bash
# POST devuelve 405 con cuerpo vacio
$ curl -sI -X POST https://the-full-stack.com/mcp
HTTP/2 405
content-length: 0

# GET devuelve 200 con HTML del SPA fallback
$ curl -sI https://the-full-stack.com/mcp
HTTP/2 200
content-type: text/html; charset=utf-8
```

### Causa raiz

`wrangler pages dev apps/generic/dist` local reproduce:

```
ERROR service core:user:...: Uncaught TypeError:
  (intermediate value).glob is not a function
  at functionsWorker-...js:5760:27
The Workers runtime failed to start.
```

El bundle `apps/<niche>/dist/functions/mcp.js` (225 KB, generado por
`postbuild-functions.mjs`) contiene en 3 lugares:

```js
var modules = import.meta.glob("./*.yaml", { eager: true })
```

Origen: `@portfolio/content/src/data/i18n/{elements,hub-selector,curriculum}/index.ts`
(loaders de i18n con Vite glob). Aunque `@portfolio/mcp` solo importa
`experiences`, `projects` y `profile`, el barrel `@portfolio/content/index.ts`
re-exporta tambien los `elements`/`hubSelector` que arrastran el glob;
esbuild no tree-shake esos modulos.

El runtime de Cloudflare Workers no implementa `import.meta.glob`
(es exclusivo de Vite). La Function falla al cargar y Pages devuelve
HTTP 405 al POST (sin handler) o cae al SPA fallback en GET.

### Decision

Fix en Fase 1: `@portfolio/mcp` deja de importar `@portfolio/content`
directamente. En su lugar, los handlers reciben un `DataProvider`
(interface) inyectado. El postbuild genera un JSON snapshot del CV en
`apps/<niche>/functions/_data/cv-snapshot.json` y la Function lo importa
estaticamente.

## Bug 2: `.well-known/*.json` sirve HTML del SPA fallback

### Sintomas

```bash
# Headers correctos, body es HTML
$ curl -s https://the-full-stack.com/.well-known/api-catalog.json | head -c 100
<!DOCTYPE html><html lang="es">...

$ curl -sI https://the-full-stack.com/.well-known/api-catalog.json
HTTP/2 200
content-type: application/linkset+json; charset=UTF-8

$ curl -s https://the-full-stack.com/.well-known/mcp/server-card.json | head -c 100
<!DOCTYPE html><html lang="es">...

# /index.md (raiz, no dotfile) SI funciona
$ curl -s https://the-full-stack.com/index.md | head -c 60
Pablo Contreras · Lima, Perú · Disponible remoto LATAM/US
```

### Causa raiz

Cloudflare Pages excluye archivos y directorios dotfiles del upload por
defecto. Doc oficial: "Cloudflare Pages does not upload files larger
than 25 MiB, hidden files (files starting with `.`), or files inside
hidden directories (directories starting with `.`)".

Como `.well-known/` empieza con `.`, los archivos dentro **NO se
suben**. La URL recibe el `Content-Type` del `_headers` (que matchea por
ruta, no por archivo) pero el cuerpo viene del SPA fallback
(`index.html`).

Confirmacion: una URL inventada `https://the-full-stack.com/.well-known/inexistente-xyz`
devuelve el mismo HTML — mismo comportamiento que el archivo "real".

### Decision

Fix en Fase 2: Opciones A -> B -> C secuenciales (detalladas en
`04-fase-2-wellknown-fix.md`).

## Bug 3: Transform Rule TR-1 nunca activada

### Sintomas

```bash
$ curl -H "Accept: text/markdown" https://the-full-stack.com/ -o /dev/null -w '%{http_code} %{content_type}\n'
200 text/html; charset=UTF-8
```

isitagentready reporta:
> `[high][contentAccessibility]` Support Accept: text/markdown content
> negotiation for machine-readable content

### Causa raiz

`cloudflare/transform-rules.md` documenta TR-1 como activacion MANUAL
en el dashboard. Nadie la activo despues del deploy. Anti-pattern: no
versionable, no CI-friendly.

### Decision

Fix en Fase 5: reemplazar Transform Rule por un Pages Function
`_middleware.ts` que hace la reescritura. Eliminar
`cloudflare/transform-rules.md`.

## Bug 4: `openapi.json` apuntado por linkset NO existe

### Sintomas

```bash
$ curl -sI https://api.portfolio.the-full-stack.com/openapi.json
HTTP/2 403  # API Gateway WAF -> no hay route definida
```

El `api-catalog.json` actual:

```json
{
  "linkset": [
    {
      "anchor": "https://the-full-stack.com",
      "service-desc": [
        { "href": "https://api.portfolio.the-full-stack.com/openapi.json",
          "type": "application/json" }
      ]
    }
  ]
}
```

isitagentready espera que el `service-desc[].href` resuelva a un OpenAPI
3.x spec valido. Al fallar (403/404), reporta "API Catalog is not valid"
o similar.

### Causa raiz

El plan ai-audit-level-3-4 asumio que el backend expondria `/openapi.json`.
No se implemento. Decision (ya validada): servir `openapi.json` estatico
**desde el portfolio mismo**, NO desde el API Gateway.

### Decision

Fix en Fase 3: nuevo builder `packages/seo/src/lib/build-openapi.ts` que
genera el spec minimo (POST /contact, GET /track). Cada app escribe
`dist/openapi.json` en prebuild. El linkset apunta a
`https://{host}/openapi.json` (mismo origen, sin dependencia del backend).

## Resumen y matriz de impacto por bug

| Bug | Score impactado | Fase de fix | Bloqueante para |
|-----|-----------------|-------------|-----------------|
| 1. MCP bundle | discovery (parcial) | Fase 1 | Fase 4, Fase 6 |
| 2. .well-known/ upload | discovery (api-catalog + mcp-server-card) | Fase 2 | Fase 6 |
| 3. Transform Rule | contentAccessibility | Fase 5 | Fase 6 |
| 4. openapi.json missing | discovery (api-catalog) | Fase 3 | Fase 6 |

Sin Fase 1, no podemos validar `/mcp` ni `/.well-known/mcp/server-card.json`
(la Function falla). Por eso Fase 1 va PRIMERA y es bloqueante.

Fases 3 y 5 son independientes entre si (paralelizables via worktrees).
