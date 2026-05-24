# 03 — Fase 2: `deploy-apps.yml` consume GH Environment Variables

## Objetivo

Modificar `.github/workflows/deploy-apps.yml` para que el build de cada
app reciba las env vars del environment destino (dev/stage/prod) y
hornee las URLs/endpoints correctos en el dist que se sube a Cloudflare
Pages.

Cumple AC-1, AC-2, AC-3, AC-8.

## Diseno

### Cambios estructurales

1. **Eliminar el reuso del artifact desde `ci.yml`** en el job
   `build-apps`. CI sigue subiendo el artifact (sirve para PRs preview),
   pero `deploy-apps.yml` siempre rebuildea con env vars correctas.
2. **Agregar `environment: ${{ stage }}`** en el job `build-apps` para
   que pueda leer `vars.*` del environment correcto.
3. **Setear `env:` block** en el step de build con todas las vars
   horneadas. La matrix por niche calcula `SITE_URL` inline.
4. **Mantener `deploy-pages`** como esta (ya hace deploy por matrix);
   solo cambia el origen del dist.

### Mapping branch -> stage -> environment

```yaml
case "$branch" in
  dev)   stage=dev;   suffix=-dev;   gh_env=dev   ;;
  stage) stage=stage; suffix=-stage; gh_env=stage ;;
  main)  stage=prod;  suffix='';     gh_env=prod  ;;
esac
```

`gh_env` es el nombre del GitHub Environment (dev/stage/prod). Las GH
Variables se leen como `${{ vars.BASE_DOMAIN }}` cuando el job declara
`environment: <gh_env>`.

### env: block del build

```yaml
- name: Build all apps with env vars
  env:
    # URL builder (consumido por packages/app-shared/src/lib/site-urls.ts)
    BASE_DOMAIN: ${{ vars.BASE_DOMAIN }}
    BASE_SCHEME: ${{ vars.BASE_SCHEME }}
    APEX_DOMAIN: ${{ vars.APEX_DOMAIN }}
    # API + Turnstile (consumido por TrackingPixel + /contact)
    PUBLIC_API_ENDPOINT: ${{ vars.PUBLIC_API_ENDPOINT }}
    PUBLIC_TURNSTILE_SITEKEY: ${{ vars.PUBLIC_TURNSTILE_SITEKEY }}
    # SITE_URL no esta en GH Vars; se setea por matrix en deploy-pages
    # via build separado del subset que necesita ese niche.
  run: pnpm -r --filter "./apps/*" --workspace-concurrency=6 run build
```

### SITE_URL por niche: dos opciones

**Opcion A (recomendada): build todas las apps con un solo SITE_URL
"placeholder" y dejar que cada app calcule el suyo via BASE_DOMAIN.**

`apps/*/astro.config.ts` hoy hace:
```ts
const SITE = process.env.SITE_URL ?? 'https://<niche>.portfolio.the-full-stack.com'
```

Cambiar a:
```ts
import { buildSiteUrl } from '@portfolio/app-shared'
const SITE = process.env.SITE_URL ?? buildSiteUrl('<niche>')
```

Asi `SITE_URL` deja de ser necesario para builds CI: `BASE_DOMAIN` +
`APEX_DOMAIN` ya alcanzan para que `buildSiteUrl` resuelva el hostname
correcto.

**Opcion B (alternativa): build por niche en la matrix, cada uno con su SITE_URL.**
Rompe el build paralelo de las 6 apps en un solo `pnpm -r` y cambia
significativamente la estructura del workflow. Mas trabajo, mismo
resultado funcional.

**Decidido**: Opcion A. Cambio menor en 6 `astro.config.ts`, build
queda igual que hoy (`pnpm -r` paralelo), `SITE_URL` ya no se necesita
como GH Variable.

### Cambios en `ci.yml`

`ci.yml` sigue construyendo dist sin env vars (defaults a prod). Como
ya no se reutiliza en deploy, eso es irrelevante para los deploys —
sirve solo para validar que el build no esta roto en PRs y para que los
preview deploys (si se agregan en el futuro) tengan un artifact.

Opcionalmente: agregar comentario en `ci.yml` aclarando que el dist
generado NO es deployable a env (URLs son defaults prod).

### Cambios en `_headers`

Inspeccion previa: el `_headers` actual de cada app ya incluye `connect-src`
con los 3 hostnames de API (`api.portfolio.the-full-stack.com`,
`api.portfolio.dev.the-full-stack.com`, `api.portfolio.stage.the-full-stack.com`).
Esta sobre-permisivo pero no roto — el browser solo conecta al endpoint
horneado en `data-api-endpoint`. **NO cambia en este plan.** Si quisieramos
limitar la CSP por env, seria un plan aparte.

## Archivos

### Modificar

- `.github/workflows/deploy-apps.yml`:
  - Agregar `environment: ${{ needs.resolve-env.outputs.stage }}` al
    job `build-apps` (NO al deploy-pages, ese no necesita las vars).
  - Quitar el step "Try to download CI artifact" — siempre rebuildear.
  - Agregar `env:` con las 5 vars al step `Build all apps`.
  - Verificar: push de prueba a `dev`, revisar logs del workflow y
    confirmar que las env vars aparecen en el step (los Variables NO
    se mascarean, asi que se ven en log).

- `apps/{generic,hub,fintech,architect,leader,vibe}/astro.config.ts`
  (6 archivos):
  - Reemplazar `process.env.SITE_URL ?? 'https://...'` por
    `process.env.SITE_URL ?? buildSiteUrl('<niche>')`.
  - Importar `buildSiteUrl` de `@portfolio/app-shared`.
  - Verificar: `pnpm --filter @portfolio/<app> exec astro check` pasa.

- `.github/workflows/ci.yml`:
  - Cambio MINIMO: agregar comentario aclarando que el artifact que
    sube NO tiene env vars (es solo para PRs preview / validacion).
  - Verificar: `gh workflow run ci.yml --ref <feature-branch>` corre OK.

### Crear

(ninguno — solo modificacion)

## Tests Requeridos

### 6.B. Unit Tests

- `packages/app-shared/tests/unit/lib/site-urls.test.ts` (ya existe):
  agregar test que cubre `buildSiteUrl('generic')` con `APEX_DOMAIN=''`
  y `BASE_DOMAIN='portfolio.dev...'` -> retorna `https://portfolio.dev...`
  (consistente con el doc de site-urls.ts: si APEX vacio, generic usa
  BASE_DOMAIN).
- Verificar: `pnpm --filter @portfolio/app-shared exec vitest run`

### 6.D. E2E (verificacion live post-deploy)

Esto va en Fase 4 (07-verificacion-e2e.md) — la verificacion E2E real
es post-merge a dev y consiste en curl + grep sobre el HTML deployado.

## Verificacion incremental (al final de la Fase 2)

```bash
# Typecheck de los 6 astro.config.ts modificados
pnpm exec astro check  # via cada app
pnpm exec tsc --noEmit

# Tests unit del package que cambia
pnpm --filter @portfolio/app-shared exec vitest run

# Build estatico funciona (con defaults locales)
pnpm run build

# Lint
pnpm exec biome check .
```

Despues del merge a `dev`, monitor del workflow:

```bash
gh run watch  # mirar el run de deploy-apps en vivo
gh run view --log | grep -E "BASE_DOMAIN|PUBLIC_API_ENDPOINT" | head -5
```
