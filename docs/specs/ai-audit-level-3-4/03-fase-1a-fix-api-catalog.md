# 03 — Fase 1A: Fix api-catalog (renombrar a `.json` + redirect 200)

> **Anterior**: [02-fase-0-diagnostico.md](02-fase-0-diagnostico.md) · **Siguiente**: [04-fase-1b-markdown-estatico.md](04-fase-1b-markdown-estatico.md)
>
> **Cubre**: AC-1, AC-2
>
> **Objetivo**: que `curl https://the-full-stack.com/.well-known/api-catalog`
> devuelva el JSON real (no el SPA fallback).

## Estrategia

1. Cambiar el path de salida del builder de `/.well-known/api-catalog` →
   `/.well-known/api-catalog.json` (asi Cloudflare reconoce la extension
   y sirve el archivo estatico directamente, sin SPA fallback).
2. Agregar redirect **200** (no 301) en `_redirects` para que la URL
   canonica RFC 9727 (`/.well-known/api-catalog`) siga sirviendo el
   mismo JSON. Redirect 200 = "internal rewrite" en Cloudflare Pages:
   el cliente recibe HTTP 200 con el contenido del path final, sin ver
   un 301.
3. Actualizar `_headers` para que `Content-Type: application/linkset+json`
   se aplique a ambos paths (con y sin `.json`).
4. Actualizar el Link header del prebuild para apuntar a `.json` (que es
   la URL canonica del archivo real); RFC 9727 no exige el path exacto
   `/.well-known/api-catalog`, sirve cualquier ruta documentada.

## Tarea 1A.1 — Modificar `packages/seo/src/lib/build-api-catalog.ts`

Solo cambia el path de salida. La firma de la funcion + el JSON son
identicos.

```ts
// Antes:
export function buildApiCatalog(params: ApiCatalogParams): string {
  const payload = { linkset: [...] }
  return `${JSON.stringify(payload, null, 2)}\n`
}

// Sin cambios — el builder solo devuelve el contenido.
// El path de salida lo decide el caller (build-public-assets.mjs).
```

**Decision**: la responsabilidad del path de salida vive en el caller,
no en el builder. El builder se queda igual. Solo se actualiza el caller.

## Tarea 1A.2 — Modificar `apps/*/scripts/build-public-assets.mjs` (6 apps)

Cambiar la linea del write del api-catalog:

```js
// Antes:
await write(
  '.well-known/api-catalog',
  buildApiCatalog({ siteUrl: SITE_URL, apiEndpoint: API_ENDPOINT }),
)

// Despues:
await write(
  '.well-known/api-catalog.json',
  buildApiCatalog({ siteUrl: SITE_URL, apiEndpoint: API_ENDPOINT }),
)
```

Aplicar en los 6 archivos via Edit tool (mismo cambio).

## Tarea 1A.3 — Actualizar `packages/seo/src/lib/build-redirects.ts`

Agregar el redirect 200 para mantener compatibilidad con la URL canonica
RFC 9727:

```ts
export function buildRedirects(): string {
  return [
    '/sitemap.xml /sitemap-index.xml 301',
    '/.well-known/api-catalog /.well-known/api-catalog.json 200',
    '',
  ].join('\n')
}
```

Nota: `200` = rewrite interno en Cloudflare Pages (cliente ve HTTP 200
del path destino, sin redirect visible). Documentado en
https://developers.cloudflare.com/pages/configuration/redirects/.

## Tarea 1A.4 — Actualizar `packages/seo/src/lib/build-headers.ts`

Cambiar el bloque del Content-Type para que aplique a ambos paths
(con y sin `.json`):

```ts
// Antes:
'/.well-known/api-catalog',
'  Content-Type: application/json',
'',

// Despues:
'/.well-known/api-catalog',
'  Content-Type: application/linkset+json; charset=UTF-8',
'',
'/.well-known/api-catalog.json',
'  Content-Type: application/linkset+json; charset=UTF-8',
'',
```

Nota: el MIME correcto segun RFC 9727 es `application/linkset+json` (no
`application/json` generico).

## Tarea 1A.5 — Actualizar el Link header del prebuild

El `Link` header en `_headers` que anuncia el api-catalog debe apuntar
a la URL canonica del archivo real (`.json`) Y/O mantener la URL RFC
9727 generica. RFC 9727 no exige el path exacto, asi que la mejor
practica es apuntar al `.json` directamente (evita el rewrite extra).

```ts
// En packages/seo/src/lib/build-headers.ts:
'  Link: </sitemap-index.xml>; rel="sitemap"',
'  Link: </llms.txt>; rel="alternate"; type="text/plain"; title="llms.txt"',
// Antes:
'  Link: </.well-known/api-catalog>; rel="api-catalog"',
// Despues:
'  Link: </.well-known/api-catalog.json>; rel="api-catalog"; type="application/linkset+json"',
```

## Tarea 1A.6 — Tests unitarios

### Modificar `packages/seo/tests/unit/build-redirects.test.ts`

Agregar test que valida el nuevo redirect:

```ts
it('Given build When inspect Then includes api-catalog rewrite 200', () => {
  const output = buildRedirects()
  expect(output).toContain(
    '/.well-known/api-catalog /.well-known/api-catalog.json 200',
  )
})
```

### Modificar `packages/seo/tests/unit/build-headers.test.ts`

Agregar tests que validan:

1. Existe bloque `/.well-known/api-catalog.json` con
   `Content-Type: application/linkset+json`.
2. Existe bloque `/.well-known/api-catalog` con el mismo header (para
   el rewrite interno).
3. El `Link: ` header apunta a `.json` con el `type` declarado.

```ts
it('Given build When inspect Then api-catalog.json has linkset+json Content-Type', () => {
  const output = buildHeaders()
  expect(output).toContain('/.well-known/api-catalog.json')
  expect(output).toMatch(
    /\/\.well-known\/api-catalog\.json\s+Content-Type: application\/linkset\+json/,
  )
})

it('Given build When inspect Then Link header points to api-catalog.json with type', () => {
  const output = buildHeaders()
  expect(output).toContain(
    '</.well-known/api-catalog.json>; rel="api-catalog"; type="application/linkset+json"',
  )
})
```

## Tarea 1A.7 — Verificar con `wrangler pages dev`

```bash
pnpm --filter @portfolio/generic run build
npx wrangler pages dev apps/generic/dist --port 8788
```

En otra terminal:

```bash
# AC-1: URL canonica RFC 9727 sirve JSON via rewrite 200
curl -s http://localhost:8788/.well-known/api-catalog | jq .
# ESPERADO: JSON parseable con linkset[0].anchor == 'https://the-full-stack.com'

# AC-2: URL directa con .json sirve JSON sin redirect
curl -s http://localhost:8788/.well-known/api-catalog.json | jq .
# ESPERADO: mismo JSON

# Content-Type
curl -sI http://localhost:8788/.well-known/api-catalog.json | grep -i content-type
# ESPERADO: content-type: application/linkset+json; charset=UTF-8
```

## Verificacion incremental (antes del commit)

```bash
# 1. Builders compilan + tests pasan
pnpm --filter @portfolio/seo run test
pnpm --filter @portfolio/seo run typecheck

# 2. Coverage del builder
pnpm --filter @portfolio/seo exec vitest run --coverage \
  src/lib/build-api-catalog.ts src/lib/build-redirects.ts src/lib/build-headers.ts
# ESPERADO: >= 80% per-file

# 3. Build de las 6 apps
pnpm run build
# ESPERADO: exitoso, dist contiene .well-known/api-catalog.json en los 6

# 4. Lint
pnpm exec biome check packages/seo apps/*/scripts/build-public-assets.mjs
```

## Archivos afectados

### Modificar

- `packages/seo/src/lib/build-redirects.ts` — agregar rewrite 200
  - Verificar: `pnpm --filter @portfolio/seo run test build-redirects` pasa
- `packages/seo/src/lib/build-headers.ts` — duplicar bloque + actualizar Link
  - Verificar: `pnpm --filter @portfolio/seo run test build-headers` pasa
- `packages/seo/tests/unit/build-redirects.test.ts` — test nuevo
- `packages/seo/tests/unit/build-headers.test.ts` — 2 tests nuevos
- `apps/architect/scripts/build-public-assets.mjs` — path `.json`
- `apps/fintech/scripts/build-public-assets.mjs` — path `.json`
- `apps/generic/scripts/build-public-assets.mjs` — path `.json`
- `apps/hub/scripts/build-public-assets.mjs` — path `.json`
- `apps/leader/scripts/build-public-assets.mjs` — path `.json`
- `apps/vibe/scripts/build-public-assets.mjs` — path `.json`
  - Verificar (los 6): `pnpm run build` exitoso + cada `apps/X/dist/.well-known/api-catalog.json` existe
- `.gitignore` — agregar `apps/*/public/.well-known/api-catalog.json` (mantener
  consistencia con `apps/*/public/.well-known/` actual)
  - Verificar: `git check-ignore -v apps/generic/public/.well-known/api-catalog.json` matchea

## Done

- [ ] Builder con tests verdes (coverage >= 80%)
- [ ] Build de las 6 apps exitoso
- [ ] `wrangler pages dev` local reproduce el fix (AC-1 + AC-2)
- [ ] Lint + typecheck verde
- [ ] Commit `fix(seo): sirve api-catalog como .json + rewrite 200 desde URL canonica`
