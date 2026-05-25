# Fase 4 - apps: actualizar 6 prebuild scripts

[< 04 devtools/validator](04-fase-devtools-validator.md) | [06 app-shared JSON-LD >](06-fase-app-shared-jsonld.md)

## Objetivo

Hacer que los 6 prebuild scripts (`apps/*/scripts/build-public-assets.mjs`)
usen los 2 builders nuevos de `packages/seo` y escriban los archivos
generados al `public/` de cada app.

## Cambios

### Diff para cada `apps/<X>/scripts/build-public-assets.mjs`

Es identico en los 6 (solo cambia `NICHE` y `SITE_URL`):

```diff
  import { profile } from '@portfolio/content'
  import { renderCvHtml } from '@portfolio/cv-pdf'
- import { buildHeaders, buildLlmsTxt, buildRobotsTxt } from '@portfolio/seo'
+ import {
+   buildApiCatalog,
+   buildHeaders,
+   buildLlmsTxt,
+   buildRedirects,
+   buildRobotsTxt,
+ } from '@portfolio/seo'

  // ...

  async function main() {
    // ... (CV HTML + cv-filters)
    // 2. llms.txt (existente)
    // 3. robots.txt (existente)
    // 4. _headers (existente, ahora con Link headers desde buildHeaders)
    await write('_headers', buildHeaders({ apiEndpoint: API_ENDPOINT }))

+   // 5. _redirects (alias sitemap.xml -> sitemap-index.xml)
+   await write('_redirects', buildRedirects())
+
+   // 6. .well-known/api-catalog (JSON RFC9727)
+   await write(
+     '.well-known/api-catalog',
+     buildApiCatalog({ siteUrl: SITE_URL, apiEndpoint: API_ENDPOINT }),
+   )
  }
```

### `write()` ya soporta subdirectorios

El helper actual hace `mkdir({recursive: true})`, asi que el path
`.well-known/api-catalog` se crea sin cambios.

## Tests

Estos scripts NO tienen unit tests propios (son glue de I/O). La
verificacion es:

1. `pnpm run build` corre los 6 prebuilds + Astro build.
2. Cada `apps/<X>/dist/` debe contener:
   - `_redirects` con el contenido esperado
   - `.well-known/api-catalog` con JSON valido

## Archivos afectados

### Modificar (6 archivos, mismo diff)

- `apps/architect/scripts/build-public-assets.mjs`
- `apps/fintech/scripts/build-public-assets.mjs`
- `apps/generic/scripts/build-public-assets.mjs`
- `apps/hub/scripts/build-public-assets.mjs`
- `apps/leader/scripts/build-public-assets.mjs`
- `apps/vibe/scripts/build-public-assets.mjs`
  - Verificar: `pnpm run build` los 6 verde
  - Verificar dist:
    ```bash
    for app in generic hub fintech architect leader vibe; do
      ls apps/$app/dist/_redirects apps/$app/dist/.well-known/api-catalog
    done
    ```
    todos deben existir.

## Verificacion incremental

```bash
pnpm run build

# Verificar archivos generados
for app in generic hub fintech architect leader vibe; do
  echo "=== $app ==="
  cat apps/$app/dist/_redirects 2>/dev/null | head -2
  jq -c . apps/$app/dist/.well-known/api-catalog 2>/dev/null | head -1
done
```

[< 04 devtools/validator](04-fase-devtools-validator.md) | [06 app-shared JSON-LD >](06-fase-app-shared-jsonld.md)
