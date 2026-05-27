# Fase 3 — `openapi.json` estatico (paralelo con Fase 5)

## Objetivo

`GET /openapi.json` devuelve un OpenAPI 3.1 spec valido con los 2
endpoints reales del backend (AC-4). El `api-catalog.json` linkset
apunta a este nuevo path.

## Estrategia

- Builder en `@portfolio/seo` que genera el OpenAPI spec.
- Prebuild de cada app escribe `dist/openapi.json` desde el builder.
- Actualizar `build-api-catalog.ts` para que `service-desc[].href`
  apunte a `https://{host}/openapi.json` (mismo origen, no al
  api.portfolio).
- Sin auth schemes, sin error responses 5xx. Solo lo minimo para que
  isitagentready vea OpenAPI 3.x valido + util como descripcion para
  agentes.

## Archivos

### Crear

- `packages/seo/src/lib/build-openapi.ts`
  - Funcion `buildOpenApi(params: { siteUrl: string }): string`.
  - Devuelve JSON serializado del spec.
  - Hardcoded:
    - `openapi: "3.1.0"`
    - `info: { title: "Pablo Contreras Portfolio API", version: "1.0.0", description: "...", contact: { name, url } }`
    - `servers: [ { url: "https://api.portfolio.the-full-stack.com" } ]`
    - `paths`:
      - `POST /contact` con request body (firstName, lastName, email,
        message, turnstileToken) + responses 202, 400, 429.
      - `GET /track` con query params (event_type, session_id, etc.) +
        response 200 image/gif.

- `packages/seo/tests/unit/build-openapi.test.ts`
  - WHEN buildOpenApi THEN devuelve OpenAPI 3.1 con 2 paths.
  - Coverage 100% per-file.

### Modificar

- `packages/seo/src/index.ts`
  - Exportar `buildOpenApi`.

- `apps/<niche>/scripts/build-public-assets.mjs` (x6)
  - Llamar a `buildOpenApi({ siteUrl })` y escribir
    `dist/openapi.json`.

- `packages/seo/src/lib/build-api-catalog.ts` (si existe — sino el
  builder vive en otro archivo, verificar en Fase 0)
  - Cambiar `service-desc[].href` para apuntar a
    `${siteUrl}/openapi.json` (no `api.portfolio.*/openapi.json`).

- `packages/seo/tests/unit/build-api-catalog.test.ts` (si existe)
  - Actualizar para reflejar el nuevo `href`.

### Eliminar

- Nada.

## Tests requeridos

- `packages/seo/tests/unit/build-openapi.test.ts` [AC-4]
- `packages/seo/tests/unit/build-api-catalog.test.ts` (modificar)

## Verificacion

```bash
# Build local
pnpm --filter @portfolio/seo run test:coverage
pnpm --filter @portfolio/generic run build  # con env vars

# Verifico dist/openapi.json
cat apps/generic/dist/openapi.json | jq .openapi
# Esperado: "3.1.0"
cat apps/generic/dist/openapi.json | jq '.paths | keys'
# Esperado: ["/contact", "/track"]

# Post-deploy a dev
curl -s https://generic.portfolio.dev.the-full-stack.com/openapi.json | jq .openapi
```

## Done cuando

- [ ] Tests verde + coverage >= 80%
- [ ] `dist/openapi.json` se genera y parsea como OpenAPI valido
- [ ] Deploy a dev + curl-check pasa
- [ ] Commit: `feat(seo): openapi.json estatico minimo (POST /contact, GET /track)`
