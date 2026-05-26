# 05 — Fase 1C: Cloudflare Transform Rule (`Accept: text/markdown` → `.md`)

> **Anterior**: [04-fase-1b-markdown-estatico.md](04-fase-1b-markdown-estatico.md) · **Siguiente**: [06-fase-2a-mcp-server-endpoint.md](06-fase-2a-mcp-server-endpoint.md)
>
> **Cubre**: AC-6
>
> **Objetivo**: que un cliente que envia `Accept: text/markdown` reciba
> el `.md` gemelo de la pagina, sin que la URL cambie publicamente.

## Estrategia

Cloudflare ofrece **Transform Rules** (Free tier compatible, 10 reglas
por zona). Una `URL Rewrite` rule:

- **Match**: `http.request.headers["accept"][0] contains "text/markdown"`
- **Rewrite**: append `.md` al path si no termina en `.md` y es una
  ruta HTML servida (no static asset)

Las Transform Rules se gestionan en el dashboard de Cloudflare o via la
API. Como devtools NO tiene flujo para Transform Rules (solo Pages
projects + DNS), la activacion es manual + documentada en `cloudflare/`.

## Tarea 1C.1 — Diseno de la regla

Expresion match:

```
(any(http.request.headers["accept"][*] contains "text/markdown"))
and (not http.request.uri.path matches "\\.(json|xml|txt|png|jpg|jpeg|gif|svg|ico|css|js|woff2?|webp|avif)$")
and (not starts_with(http.request.uri.path, "/.well-known/"))
and (not starts_with(http.request.uri.path, "/mcp"))
```

Razon de los `not`:
- Excluir static assets (no tienen `.md` gemelo)
- Excluir `/.well-known/` (sus archivos son JSON, no HTML)
- Excluir `/mcp` (Pages Function, no pagina HTML)

Rewrite action: dynamic, expression:

```
concat(http.request.uri.path, ".md")
```

Pero la regla tiene un edge case: el path puede terminar en `/`
(directorio). Hay que normalizar:
- `/about/` → `/about/index.md` (no `/about/.md`)
- `/about` → `/about/index.md` o `/about.md` segun como Astro builda

Astro builda por defecto `dist/about/index.html` (directory style). El
postbuild de Fase 1B genera `dist/about/index.md`. Asi que el rewrite
correcto es: si termina en `/`, append `index.md`; si no, append `/index.md`.

Expresion mejorada:

```
concat(
  http.request.uri.path,
  if(ends_with(http.request.uri.path, "/"), "index.md", "/index.md")
)
```

## Tarea 1C.2 — Aplicar a las 6 Pages projects + apex

Las 6 Pages projects + el apex viven bajo la zona DNS
`the-full-stack.com`. Una sola Transform Rule a nivel de zona cubre los
6 subdominios + el apex.

Comando con la API (opcional, para automatizacion futura):

```bash
ZONE_ID=$(curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones?name=the-full-stack.com" \
  | jq -r '.result[0].id')

curl -X POST \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/rulesets/phases/http_request_transform/entrypoint" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rules": [{
      "description": "Serve Markdown to agents requesting text/markdown",
      "expression": "(any(http.request.headers[\"accept\"][*] contains \"text/markdown\")) and (not http.request.uri.path matches \"\\\\.(json|xml|txt|png|jpg|jpeg|gif|svg|ico|css|js|woff2?|webp|avif)$\") and (not starts_with(http.request.uri.path, \"/.well-known/\")) and (not starts_with(http.request.uri.path, \"/mcp\"))",
      "action": "rewrite",
      "action_parameters": {
        "uri": {
          "path": {
            "expression": "concat(http.request.uri.path, if(ends_with(http.request.uri.path, \"/\"), \"index.md\", \"/index.md\"))"
          }
        }
      }
    }]
  }'
```

**Decision**: aplicar la regla MANUALMENTE desde el dashboard
(Cloudflare → the-full-stack.com → Rules → Transform Rules → URL
Rewrites) en este plan. Documentar el comando API arriba como
referencia para automatizacion futura (no scope de este plan).

## Tarea 1C.3 — Documentar en `cloudflare/transform-rules.md`

Crear `cloudflare/transform-rules.md` con:

1. Lista de Transform Rules activas
2. Para cada una: nombre, expresion match, accion, justificacion,
   cuando crearla, como verificarla
3. Comando API equivalente (para auditoria o disaster recovery)
4. Limites del free tier (10 rules por zona)

## Tarea 1C.4 — Actualizar `_headers` para `.md`

Agregar bloque que setea `Content-Type: text/markdown; charset=UTF-8`
para archivos `.md`:

```ts
// En packages/seo/src/lib/build-headers.ts:
'/*.md',
'  Content-Type: text/markdown; charset=UTF-8',
'',
```

Y test en `build-headers.test.ts`:

```ts
it('Given build When inspect Then .md has text/markdown Content-Type', () => {
  const out = buildHeaders()
  expect(out).toContain('/*.md')
  expect(out).toMatch(/\/\*\.md\s+Content-Type: text\/markdown/)
})
```

## Verificacion incremental

```bash
# Tests pasan
pnpm --filter @portfolio/seo run test

# Manual post-deploy a dev: simular request de agente
curl -H 'Accept: text/markdown' -L https://generic.portfolio.dev.the-full-stack.com/about
# ESPERADO: respuesta en Markdown (no HTML), content-type: text/markdown
```

## Archivos afectados

### Crear

- `cloudflare/transform-rules.md` — documentacion de la regla
  - Verificar: `pnpm exec biome check cloudflare/`

### Modificar

- `packages/seo/src/lib/build-headers.ts` — bloque `.md`
  - Verificar: test pasa
- `packages/seo/tests/unit/build-headers.test.ts` — test nuevo

### Manual (NO se commitea — documentado en `cloudflare/transform-rules.md`)

- Activar Transform Rule en dashboard Cloudflare (zona
  `the-full-stack.com`)
- Verificar despues con `curl -H 'Accept: text/markdown'`

## Done

- [ ] Documentacion `cloudflare/transform-rules.md` lista
- [ ] `_headers` actualizado con bloque `.md`
- [ ] Tests verde + coverage
- [ ] Commit `feat(seo,docs): Content-Type text/markdown para .md + documenta Transform Rule`
- [ ] Transform Rule activada manualmente en dashboard (registrar fecha
  + screenshot en `cloudflare/transform-rules.md`)
