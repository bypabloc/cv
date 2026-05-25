# Fase 5 - packages/app-shared: incluir WebSite JSON-LD en layout

[< 05 prebuild scripts](05-fase-prebuild-scripts.md) | [07 validar skills >](07-fase-validar-skills.md)

## Objetivo

Inyectar el JSON-LD `WebSite` (generado por `buildWebSiteSchema` de
`packages/seo`) en el `<head>` de las 6 apps, junto al `ProfilePage`
existente. Crawlers IA + Google podran identificar "el nombre del
sitio" + idiomas soportados.

## Cambios

### Donde vive el JSON-LD actual

`packages/app-shared` provee el layout compartido (`SitePageLayout`
o similar). Ahi se inyecta el JSON-LD del `<head>`. Necesita:

1. Importar `buildWebSiteSchema` desde `@portfolio/seo`.
2. Llamar a ambos builders (`ProfilePage` ya existe + `WebSite` nuevo).
3. Inyectar AMBOS via `@graph` (preferido por crawlers) o como 2
   `<script type="application/ld+json">` separados.

### Snippet esperado en el HTML rendered

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "ProfilePage", "dateModified": "...", "mainEntity": {...} },
    { "@type": "WebSite", "name": "...", "url": "...", "inLanguage": ["es","en"] }
  ]
}
</script>
```

(Si la implementacion actual no usa `@graph`, podemos inyectar 2
scripts separados — crawlers aceptan ambas formas.)

### Investigacion previa antes de implementar

Antes de codear la fase, revisar:

1. `packages/app-shared/src/` para encontrar donde se renderiza el
   JSON-LD actual.
2. Si la API es `buildProfilePageSchema().json` o devuelve objeto JS,
   ver como combinarlo con el nuevo.
3. Verificar si el layout permite mas de un `<script type="application/ld+json">`
   (Astro slot al `<head>`).

Es probable que sea un cambio de 5-10 lineas en 1-2 archivos.

## Tests

`packages/app-shared/tests/unit/`:

- Test que asserting el HTML rendered del layout incluye AMBOS
  `@type=ProfilePage` y `@type=WebSite` (string match o parsear JSON-LD).

Si el package no tiene tests, agregar uno minimo.

## Archivos afectados

### Modificar

- `packages/app-shared/src/<layout>.astro` o `<jsonld>.ts` (depende
  de la arquitectura — investigar en fase de exec)
  - Verificar: `pnpm --filter @portfolio/app-shared run test`
  - Verificar: `pnpm run build` los 6
  - Verificar post-build:
    ```bash
    for app in generic hub fintech architect leader vibe; do
      grep -c '"@type":"WebSite"' apps/$app/dist/index.html || echo "FAIL $app"
    done
    ```
    los 6 deben imprimir >= 1.

### (Posible) Crear

- `packages/app-shared/tests/unit/jsonld.test.ts` si no existe.

## Verificacion incremental

```bash
pnpm --filter @portfolio/app-shared run test
pnpm run build

# Confirmar en cada dist
for app in generic hub fintech architect leader vibe; do
  count=$(grep -c '"@type":"WebSite"' apps/$app/dist/index.html)
  echo "$app: $count match(es) de WebSite"
done
```

[< 05 prebuild scripts](05-fase-prebuild-scripts.md) | [07 validar skills >](07-fase-validar-skills.md)
