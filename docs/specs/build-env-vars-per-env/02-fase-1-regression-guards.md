# 02 — Fase 1: Regression guards (las 3 capas)

## Objetivo

Cerrar el hueco que dejo pasar el bug del `/track` desplegado roto:
ningun test ni guard fail-fast detectaba que el build se ejecuto sin
`PUBLIC_API_ENDPOINT`. Agregar tres capas defensivas COMPLEMENTARIAS
que tienen que pasar antes de que el deploy salga.

Cumple AC-9 (el plan no es "listo" sin las 3 capas verdes).

## Capas

### Capa A — Build-time guard en componentes Astro

Hacer que el build falle si las env vars criticas estan vacias **o
incoherentes con el resto del build**. Hoy, una prop vacia se traduce
en un atributo HTML omitido y el script se autodesactiva en silencio.

**Componentes con guard**:

- `packages/ui/src/components/TrackingPixel.astro` — guard de
  `PUBLIC_API_ENDPOINT`.
- `packages/ui/src/components/ContactFormReact.astro` (wrapper Astro
  del form) o el page `/contact` de cada app — guard de
  `PUBLIC_API_ENDPOINT` y `PUBLIC_TURNSTILE_SITEKEY`.

**Reglas del guard**:

El guard valida DOS condiciones (decision: "vacio + match contra
regex por env"):

1. **No vacio**: `apiEndpoint` no puede ser `undefined`, `null` ni `''`.
2. **Coherente con `BASE_DOMAIN`**: si `BASE_DOMAIN` esta seteado
   (caso CI/deploy), el `apiEndpoint` DEBE ser
   `https://api.${BASE_DOMAIN}`. Si no matchea, error claro con
   ambos valores.

Pseudocodigo:

```ts
// En packages/app-shared/src/lib/validate-build-env.ts (modulo nuevo)
export function validateApiEndpoint(apiEndpoint: string | undefined): string {
  if (!apiEndpoint) {
    throw new Error(
      'PUBLIC_API_ENDPOINT vacio en el build. Setealo en el env del job ' +
      'de CI (deploy-apps.yml) o en docker/env/client/.{env} para local.'
    )
  }
  const baseDomain = process.env.BASE_DOMAIN
  if (baseDomain) {
    const expected = `https://api.${baseDomain}`
    if (apiEndpoint !== expected) {
      throw new Error(
        `PUBLIC_API_ENDPOINT (${apiEndpoint}) no matchea BASE_DOMAIN ` +
        `(${baseDomain}). Esperado: ${expected}. Revisa GitHub ` +
        `Environment Variables del env destino.`
      )
    }
  }
  return apiEndpoint
}
```

Y en `TrackingPixel.astro`:

```astro
---
import { validateApiEndpoint } from '@portfolio/app-shared'
const { apiEndpoint: rawApi, niche = 'generic' } = Astro.props
const apiEndpoint = validateApiEndpoint(rawApi)
---
```

> Trade-off del strict mode: si alguien builda local sin `BASE_DOMAIN`
> pero con `PUBLIC_API_ENDPOINT=https://localhost:8080`, el guard pasa
> (porque sin `BASE_DOMAIN` no exige match). Si seteo `BASE_DOMAIN` y
> me equivoco al copiar la URL, falla con mensaje claro — eso es el
> comportamiento deseado.

### Capa B — Unit test que builda apps con env vars y verifica el dist

Test que invoca `pnpm build` de UN app (hub, como representante) con
env vars conocidas, y assertea contra `dist/index.html`:

1. `<div id="cf-tracking-pixel" ... data-api-endpoint="<expected>">`
2. Los hrefs del dropdown contienen `<expected_base_domain>`
3. `<link rel="canonical" href="<expected_apex>...">`

Vive en `packages/ui/tests/build/tracking-pixel-build.test.ts` (carpeta
nueva `tests/build/` porque es un test de build, no unit puro).

```ts
import { execSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { describe, it, expect, beforeAll } from 'vitest'

describe('TrackingPixel build-time wiring', () => {
  const ENV = {
    BASE_DOMAIN: 'portfolio.dev.the-full-stack.com',
    BASE_SCHEME: 'https',
    PUBLIC_API_ENDPOINT: 'https://api.portfolio.dev.the-full-stack.com',
    PUBLIC_TURNSTILE_SITEKEY: '0x0000000000000000_dev_test',
  }

  beforeAll(() => {
    execSync('pnpm --filter @portfolio/hub run build', {
      env: { ...process.env, ...ENV },
      stdio: 'pipe',
    })
  }, 60_000)

  it('Given build con BASE_DOMAIN=dev When inspecciono dist/index.html Then data-api-endpoint matchea PUBLIC_API_ENDPOINT', () => {
    const html = readFileSync('apps/hub/dist/index.html', 'utf-8')
    expect(html).toContain('data-api-endpoint="https://api.portfolio.dev.the-full-stack.com"')
  })

  it('Given build con BASE_DOMAIN=dev When inspecciono hrefs Then NO apuntan a prod', () => {
    const html = readFileSync('apps/hub/dist/index.html', 'utf-8')
    expect(html).not.toMatch(/href="https?:\/\/[^"]*portfolio\.the-full-stack\.com[^"]*"/)
  })

  it('Given build SIN PUBLIC_API_ENDPOINT When ejecuto pnpm build Then falla con mensaje claro', () => {
    expect(() =>
      execSync('pnpm --filter @portfolio/hub run build', {
        env: { ...process.env, PUBLIC_API_ENDPOINT: '' },
        stdio: 'pipe',
      }),
    ).toThrow(/PUBLIC_API_ENDPOINT vacio/)
  })
})
```

**Costo**: ~60s por corrida (un build completo de hub). Va detras de
un flag de CI o se corre solo cuando cambian archivos en
`packages/ui/src/components/` o `packages/app-shared/src/lib/`. Si se
incluye en el pre-push, sube el tiempo del hook 60s — aceptable porque
hoy el pre-push ya corre los 6 builds en paralelo.

### Capa C — Post-deploy smoke test (curl + grep)

Job nuevo `verify-deploy` en `deploy-apps.yml`, `needs: deploy-pages`:

```yaml
verify-deploy:
  name: Verify ${{ matrix.niche }} dist matches env
  needs: [resolve-env, deploy-pages]
  runs-on: ubuntu-24.04
  if: needs.deploy-pages.result == 'success'
  strategy:
    fail-fast: false
    matrix:
      niche: [generic, hub, fintech, architect, leader, vibe]
  steps:
    - name: Resolve expected URL
      id: url
      run: |
        stage="${{ needs.resolve-env.outputs.stage }}"
        if [[ "$stage" == "prod" && "${{ matrix.niche }}" == "generic" ]]; then
          url="https://the-full-stack.com"
        elif [[ "$stage" == "prod" ]]; then
          url="https://${{ matrix.niche }}.portfolio.the-full-stack.com"
        else
          url="https://${{ matrix.niche }}.portfolio.${stage}.the-full-stack.com"
        fi
        echo "url=$url" >> "$GITHUB_OUTPUT"
        echo "expected_api=https://api.portfolio.${stage}${{ stage == 'prod' && '.the-full-stack.com' || '.the-full-stack.com' }}" >> "$GITHUB_OUTPUT"

    - name: Curl + assert data-api-endpoint
      run: |
        html=$(curl -fsSL --max-time 20 "${{ steps.url.outputs.url }}/")
        if ! grep -qF "data-api-endpoint=\"${{ steps.url.outputs.expected_api }}\"" <<<"$html"; then
          echo "::error::data-api-endpoint missing or wrong in ${{ steps.url.outputs.url }}"
          echo "$html" | grep -oE 'cf-tracking-pixel[^>]*' | head -3
          exit 1
        fi

    - name: Curl + assert dropdown hrefs match env
      run: |
        html=$(curl -fsSL --max-time 20 "${{ steps.url.outputs.url }}/")
        bad=$(grep -oE 'href="https://[^"]*portfolio\.the-full-stack\.com[^"]*"' <<<"$html" | head -3 || true)
        stage="${{ needs.resolve-env.outputs.stage }}"
        if [[ "$stage" != "prod" && -n "$bad" ]]; then
          echo "::error::Dropdown hrefs apuntan a prod desde $stage:"
          echo "$bad"
          exit 1
        fi
```

Cubre el caso que Capas A y B no atrapan: drift entre lo que se sube y
lo que Cloudflare sirve (cache stale, deploy parcial, etc.).

Costo: ~5s por niche x 6 niches = ~30s total. Insignificante.

## Archivos

### Crear

- `packages/app-shared/src/lib/validate-build-env.ts` — modulo con
  `validateApiEndpoint` y `validateTurnstileSitekey`.
  - Verificar: unit test cubre los 4 escenarios (vacio, no matchea
    BASE_DOMAIN, matchea, BASE_DOMAIN ausente)
- `packages/app-shared/tests/unit/lib/validate-build-env.test.ts`
  - Verificar: `pnpm --filter @portfolio/app-shared exec vitest run`
- `packages/ui/tests/build/tracking-pixel-build.test.ts` — Capa B
  - Verificar: `pnpm --filter @portfolio/ui exec vitest run tests/build/`
- `packages/ui/vitest.config.ts` — agregar `tests/build/` al
  `test.include` Y darle un `testTimeout` mayor (90s).

### Modificar

- `packages/ui/src/components/TrackingPixel.astro` — agregar guard
  via `validateApiEndpoint(Astro.props.apiEndpoint)`
- `packages/app-shared/src/index.ts` — exportar `validateApiEndpoint`,
  `validateTurnstileSitekey`
- `.github/workflows/deploy-apps.yml` — agregar el job
  `verify-deploy` (Capa C); el resto del workflow se modifica en
  Fase 3, pero el job de verify se puede agregar aqui porque solo
  necesita la URL canonica que ya existe en el report job
- `.git-hooks/pre-push` — agregar la Capa B como step. Si esta detras
  de un flag `RUN_BUILD_TESTS=1` por velocidad, mejor.

## Tests Requeridos

### Capa A (unit)
- `test_validateApiEndpoint_throws_on_empty`
- `test_validateApiEndpoint_throws_on_base_domain_mismatch`
- `test_validateApiEndpoint_passes_when_consistent`
- `test_validateApiEndpoint_passes_when_no_base_domain_set` (local sin docker)

### Capa B (build-test)
- `test_dist_contains_data_api_endpoint_matching_env`
- `test_dist_dropdown_hrefs_match_env`
- `test_build_without_api_endpoint_fails`

### Capa C
- Se valida en el primer push a `dev` post-merge (no hay test unit;
  el job ES el test).

## Verificacion incremental (al final de la Fase 1)

```bash
# Unit tests de validate-build-env
pnpm --filter @portfolio/app-shared exec vitest run

# Build-test de tracking pixel
pnpm --filter @portfolio/ui exec vitest run tests/build/

# Reproducir el bug original: build sin env vars debe fallar
env -u PUBLIC_API_ENDPOINT pnpm --filter @portfolio/hub run build \
  && echo "FAIL: el build deberia haber fallado" \
  || echo "OK: el build fallo con guard"

# Lint
pnpm exec biome check .
```
