# Fase 1 - packages/seo: 3 builders nuevos + actualizar buildHeaders

[< 01 Contexto](01-contexto-y-decision.md) | [03 packages/ui >](03-fase-packages-ui-tokens.md)

## Objetivo

Centralizar en `packages/seo` toda la logica de generacion de
artefactos compartidos por las 6 apps:

1. Actualizar `buildHeaders` para agregar directivas `Link` y
   override de `Content-Type` para `.well-known/api-catalog`.
2. Crear `buildRedirects` (genera `_redirects` con alias sitemap).
3. Crear `buildApiCatalog` (JSON RFC9727 con endpoints serverless).
4. Crear `buildWebSiteSchema` (JSON-LD `WebSite`).

## Cambios

### A. Actualizar `packages/seo/src/lib/build-headers.ts`

Agregar 3 directivas `Link` al bloque `/*` y un nuevo bloque
`/.well-known/api-catalog` con `Content-Type: application/json`:

```diff
  /*
    Strict-Transport-Security: ...
    (...CSP, Permissions-Policy, X-Frame-Options...)
+   Link: </sitemap-index.xml>; rel="sitemap"
+   Link: </llms.txt>; rel="alternate"; type="text/plain"; title="llms.txt"
+   Link: </.well-known/api-catalog>; rel="api-catalog"
+
+ /.well-known/api-catalog
+   Content-Type: application/json
```

### B. Crear `packages/seo/src/lib/build-redirects.ts`

```ts
/**
 * @function buildRedirects
 * @description Genera contenido de _redirects (Cloudflare Pages).
 *   Hoy solo redirige /sitemap.xml -> /sitemap-index.xml para
 *   compat con crawlers que solo chequean el path canonico.
 */
export function buildRedirects(): string {
  return '/sitemap.xml /sitemap-index.xml 301\n'
}
```

### C. Crear `packages/seo/src/lib/build-api-catalog.ts`

```ts
/**
 * @function buildApiCatalog
 * @description Genera JSON RFC9727 (linkset) apuntando al openapi.json
 *   del backend serverless del portfolio. Hace descubrible la API
 *   publica para crawlers IA.
 */
interface ApiCatalogParams {
  siteUrl: string
  apiEndpoint: string
}

export function buildApiCatalog({ siteUrl, apiEndpoint }: ApiCatalogParams): string {
  const payload = {
    linkset: [
      {
        anchor: siteUrl,
        'service-desc': [
          {
            href: `${apiEndpoint}/openapi.json`,
            type: 'application/json',
          },
        ],
      },
    ],
  }
  return `${JSON.stringify(payload, null, 2)}\n`
}
```

### D. Crear `packages/seo/src/lib/build-website-schema.ts`

```ts
/**
 * @function buildWebSiteSchema
 * @description Genera JSON-LD schema.org WebSite. Complementa al
 *   ProfilePage (que ya existe) y le da a los crawlers el "nombre
 *   del sitio" + idiomas soportados.
 */
interface WebSiteSchemaParams {
  siteUrl: string
  name: string
  inLanguage?: string[]
}

export function buildWebSiteSchema(params: WebSiteSchemaParams): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: params.name,
    url: params.siteUrl,
    inLanguage: params.inLanguage ?? ['es', 'en'],
  }
}
```

### E. Re-exportar en `packages/seo/src/index.ts`

```diff
  export { buildHeaders } from './lib/build-headers'
  export { buildLlmsTxt } from './lib/build-llms-txt'
  export { buildPersonSchema } from './lib/build-person-schema'
  export { buildProfilePageSchema } from './lib/build-profile-page-schema'
  export { buildSiteNavigationSchema } from './lib/build-site-navigation-schema'
  export { buildRobotsTxt, buildSitemap, isNonProdHost } from './lib/build-sitemap'
+ export { buildApiCatalog } from './lib/build-api-catalog'
+ export { buildRedirects } from './lib/build-redirects'
+ export { buildWebSiteSchema } from './lib/build-website-schema'
```

## Tests

`packages/seo/tests/unit/`:

- `build-headers.test.ts` (existente): actualizar para asserting las
  3 lineas `Link` + bloque `.well-known/api-catalog`.
- `build-redirects.test.ts` (nuevo): asserting contenido exacto.
- `build-api-catalog.test.ts` (nuevo): asserting JSON valido +
  shape `{linkset: [...]}` con `service-desc`.
- `build-website-schema.test.ts` (nuevo): asserting `@context`,
  `@type`, `name`, `url`, `inLanguage`.

Patron AAA + BDD-style (heredado del proyecto):

```ts
describe('buildApiCatalog', () => {
  it('Given siteUrl y apiEndpoint When build Then JSON valido con linkset', () => {
    // Arrange + Act + Assert
  })
})
```

## Archivos afectados

### Modificar

- `packages/seo/src/lib/build-headers.ts` — agregar Link headers + bloque api-catalog
  - Verificar: `pnpm --filter @portfolio/seo run test`
- `packages/seo/src/index.ts` — re-exportar las 3 nuevas
  - Verificar: `pnpm exec tsc --noEmit`
- `packages/seo/tests/unit/build-headers.test.ts` — actualizar
  - Verificar: `pnpm --filter @portfolio/seo run test`

### Crear

- `packages/seo/src/lib/build-redirects.ts`
- `packages/seo/src/lib/build-api-catalog.ts`
- `packages/seo/src/lib/build-website-schema.ts`
- `packages/seo/tests/unit/build-redirects.test.ts`
- `packages/seo/tests/unit/build-api-catalog.test.ts`
- `packages/seo/tests/unit/build-website-schema.test.ts`
  - Verificar (cada uno): `pnpm --filter @portfolio/seo exec vitest run`
  - Coverage >= 80% per-file (politica del proyecto)

## Verificacion incremental

```bash
# Tests del package
pnpm --filter @portfolio/seo run test

# Typecheck
pnpm exec tsc --noEmit

# Lint
pnpm exec biome check packages/seo
```

[< 01 Contexto](01-contexto-y-decision.md) | [03 packages/ui >](03-fase-packages-ui-tokens.md)
