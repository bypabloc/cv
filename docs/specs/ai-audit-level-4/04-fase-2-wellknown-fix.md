# Fase 2 — Fix `.well-known/` (3 opciones secuenciales)

## Objetivo

`GET /.well-known/api-catalog.json` y `GET /.well-known/mcp/server-card.json`
devuelven JSON valido (AC-2, AC-3) en dev y luego en prod.

## Estrategia: probar A -> B -> C en orden

Cada opcion se prueba aislada en dev. Si funciona, se confirma con curl
contra `https://generic.portfolio.dev.the-full-stack.com`. Si NO funciona
en ~30 min de iteracion, se descarta y se prueba la siguiente.

## Opcion A — Pages Functions

### Decisiones

- `.well-known/api-catalog.json` -> Pages Function
  `functions/.well-known/api-catalog.json.ts` (file-based routing).
- `.well-known/mcp/server-card.json` -> Pages Function
  `functions/.well-known/mcp/server-card.json.ts`.
- El JSON estatico se genera en el postbuild (mismo flujo que el
  snapshot del MCP) y vive en `apps/<niche>/functions/_data/`.
- Cada Function lee el JSON y devuelve Response con Content-Type correcto.
- Eliminar `dist/.well-known/*.json` del output de
  `build-public-assets.mjs` (ya no son assets — Functions los reemplazan).
- Eliminar entradas relacionadas de `_headers` y `_redirects` (las
  Functions devuelven sus propios headers).

### Archivos

#### Crear

- `apps/<niche>/functions/.well-known/api-catalog.json.ts` (x6)
  - Importa `./_data/api-catalog.json`, devuelve Response con
    `application/linkset+json`.

- `apps/<niche>/functions/.well-known/mcp/server-card.json.ts` (x6)
  - Importa `./_data/mcp-server-card.json`, devuelve Response con
    `application/json`.

- `apps/<niche>/scripts/postbuild-wellknown-snapshot.mjs` (x6)
  - Llama a `buildApiCatalog()` y `buildMcpServerCard()` de
    `@portfolio/seo` y escribe los JSON en
    `apps/<niche>/functions/_data/api-catalog.json` y
    `apps/<niche>/functions/_data/mcp-server-card.json`.
  - O integrar en el postbuild-mcp-snapshot (un solo script
    `postbuild-functions-data.mjs`).

#### Modificar

- `apps/<niche>/scripts/build-public-assets.mjs` (x6)
  - Eliminar la generacion de `dist/.well-known/api-catalog.json` y
    `dist/.well-known/mcp/server-card.json` (ya no son assets).
  - Eliminar el cleanup legacy de `dist/.well-known/api-catalog` (ya
    no aplica — el rewrite tampoco aplica).

- `packages/seo/src/lib/build-headers.ts`
  - Eliminar los bloques `Content-Type` de
    `/.well-known/api-catalog`,
    `/.well-known/api-catalog.json` y
    `/.well-known/mcp/server-card.json` (las Functions devuelven sus
    headers).
  - Mantener `/*.md` (el `index.md` SI funciona via _headers).
  - Mantener los `Link:` headers que apuntan a `/.well-known/*` (URLs
    canonicas independiente de quien las sirva).

- `packages/seo/src/lib/build-redirects.ts`
  - Eliminar `/.well-known/api-catalog /.well-known/api-catalog.json 200`
    (ya no aplica — las URLs canonicas las sirve directamente la
    Function, no hay rewrite).

- `packages/seo/tests/unit/build-headers.test.ts`
  - Actualizar para reflejar la eliminacion de los bloques de
    `.well-known/`.

- `packages/seo/tests/unit/build-redirects.test.ts`
  - Actualizar para reflejar la eliminacion del rewrite.

- `apps/<niche>/functions/_data/.gitignore`
  - Agregar `api-catalog.json` y `mcp-server-card.json`.

### Tests

- `packages/seo/tests/unit/build-headers.test.ts` (modificar) [AC-2, AC-3]
- `packages/seo/tests/unit/build-redirects.test.ts` (modificar)

### Verificacion local (wrangler pages dev)

```bash
cd apps/generic && pnpm run build  # con env vars
npx wrangler@latest pages dev dist --port 8789 --compatibility-date=2026-05-27 &
sleep 8
curl -s localhost:8789/.well-known/api-catalog.json | jq .
# Esperado: JSON valido con .linkset
curl -s localhost:8789/.well-known/mcp/server-card.json | jq .protocolVersion
# Esperado: "2025-11-25"
pkill -f 'wrangler.*pages.*dev'
```

### Verificacion dev (post-deploy)

```bash
curl -s https://generic.portfolio.dev.the-full-stack.com/.well-known/api-catalog.json | jq .
curl -s https://generic.portfolio.dev.the-full-stack.com/.well-known/mcp/server-card.json | jq .
```

### Done cuando

- [ ] Tests verde
- [ ] Wrangler dev local responde JSON valido en ambos endpoints
- [ ] Deploy a dev + curl-check pasa en `*.portfolio.dev.the-full-stack.com`
- [ ] Commit: `feat(seo,functions): sirve .well-known/*.json via Pages Functions`

### Si A falla

Posibles motivos:
- Pages no aplica file-based routing a `functions/.well-known/` (dotdir
  igualmente excluido).
- El bundle no se carga (otro problema parecido al de MCP).
- Conflicto con otro middleware.

Pasar a Opcion B.

## Opcion B — `wrangler.toml` con `[assets]`

### Decisiones

- Crear `apps/<niche>/wrangler.toml` con configuracion que incluye
  dotfiles en el upload.

### Investigacion previa requerida

- Documentacion wrangler 4.x para Pages: ¿soporta `[assets] not_found_handling`
  o `[assets] include`? Validar con `wrangler --help pages deploy`.
- Si la sintaxis correcta es:
  ```toml
  pages_build_output_dir = "./dist"
  compatibility_date = "2026-05-27"

  [[assets.bindings]]
  type = "static"
  directory = "./dist"
  include = [".well-known/**"]
  ```
- Modificar `deploy-apps.yml` para pasar `--config wrangler.toml`.

### Riesgo

- `wrangler pages` historicamente tiene soporte limitado de
  `wrangler.toml` (vs `wrangler` para Workers que lo usa siempre).
- Puede no funcionar en absoluto.

### Done cuando

- [ ] `wrangler pages dev` local sirve archivos en `.well-known/`
- [ ] Deploy a dev + curl-check pasa

### Si B falla

Pasar a Opcion C.

## Opcion C — `.assetsignore` con `!.well-known/**`

### Decisiones

- Crear `apps/<niche>/dist/.assetsignore` (generado en postbuild) con:
  ```
  !.well-known/**
  ```
- El `!` es sintaxis de inclusion negativa (similar a gitignore).
- Wrangler 4.x soporta `.assetsignore` para customizar la exclusion
  default.

### Investigacion previa requerida

- Confirmar sintaxis exacta (`!.well-known/`, `!/.well-known/`, etc.).
- Verificar version minima de wrangler con soporte.

### Done cuando

- [ ] `wrangler pages deploy dist` sube `dist/.well-known/*` (verificar
  con `wrangler pages download` o curl al deploy URL temporal).
- [ ] curl-check en dev pasa.

### Si C falla

Investigacion exhaustiva web:
- "Cloudflare Pages serve well-known directory"
- "wrangler pages dotfiles"
- "Cloudflare Pages free tier serve .well-known"
- Documentacion stack: Astro 6 + Cloudflare Pages + wrangler 4.

Si NADA funciona, considerar:
- Servir el contenido de `.well-known/` desde rutas alternativas:
  `/wellknown/api-catalog.json` + `Link:` headers actualizados.
  (Subóptimo: rompe la convencion IETF; isitagentready puede no
  encontrarlo).
- Migrar a Cloudflare Workers con Assets binding (nuevo modelo
  post-Pages que SI soporta dotfiles).
- Re-enviar plan con un approach diferente.
