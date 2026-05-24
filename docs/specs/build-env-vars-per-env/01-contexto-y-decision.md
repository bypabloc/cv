# 01 — Contexto y decision

## 1. Problema

Las 6 apps Astro desplegadas a Cloudflare Pages `dev`/`stage` tienen tres
sintomas, todos verificables en HTML live:

1. El dropdown "Otras vistas" linkea a la URL de **produccion** (no a
   `*.portfolio.dev.*` desde dev).
2. El componente `TrackingPixel` no emite `POST /track` — el div
   `<div id="cf-tracking-pixel">` se renderiza sin `data-api-endpoint`,
   y el script se autodesactiva con `if (host && apiEndpoint)`.
3. Las metas `og:url`, `canonical`, JSON-LD `Person.url`, hreflang y el
   sitemap apuntan a hostnames de produccion.

### Hallazgos de exploracion

- [packages/app-shared/src/lib/site-urls.ts](../../../packages/app-shared/src/lib/site-urls.ts)
  lee `BASE_DOMAIN`, `BASE_SCHEME`, `BASE_PORT`, `APEX_DOMAIN` con
  `readEnv()`. Si todas estan vacias, cae al fallback prod
  (`portfolio.the-full-stack.com` + apex `the-full-stack.com`).
- [packages/ui/src/components/TrackingPixel.astro:54](../../../packages/ui/src/components/TrackingPixel.astro#L54)
  desactiva el tracking si `data-api-endpoint` viene vacio. Astro omite
  el atributo cuando la prop es `undefined`, asi que el guard se cumple
  silenciosamente.
- [apps/*/astro.config.ts](../../../apps/fintech/astro.config.ts) define
  `SITE = process.env.SITE_URL ?? 'https://...the-full-stack.com'`. Sin
  `SITE_URL` env var, todos los `astro:assets` y meta tags usan el
  hostname de prod.
- [.github/workflows/deploy-apps.yml](../../../.github/workflows/deploy-apps.yml)
  hace `pnpm -r --filter "./apps/*" run build` sin un `env:` block: no
  pasa ninguna de las vars de arriba al build. El artifact que se
  publica a Cloudflare Pages dev queda con defaults de prod.
- [.github/workflows/ci.yml:75-78](../../../.github/workflows/ci.yml#L75)
  sube el dist como `dist-all-apps-<sha>` y `deploy-apps.yml` lo
  reutiliza si esta disponible (`continue-on-error: true` en el
  download). Mismo problema heredado.
- `gh secret list` solo expone `CLOUDFLARE_ACCOUNT_ID` y
  `CLOUDFLARE_API_TOKEN`. No hay GitHub Environments configurados.

Verificacion (live, 2026-05-24):

```bash
curl -s https://fintech.portfolio.dev.the-full-stack.com/ \
  | grep -oE 'cf-tracking-pixel[^>]*'
# cf-tracking-pixel" hidden data-niche="fintech" data-page-load=...
# NO hay data-api-endpoint -> tracking desactivado
```

## 2. Solucion Propuesta

Inyectar las env vars necesarias al BUILD de Astro segun el env destino,
y crear un script que sincronice `docker/env/client/.{env}` a GitHub
Environments para mantener los valores fuera del repo.

Tres fases secuenciales:

1. **Script `devtools/github_sync`**: lee `docker/env/client/.{env}`,
   parsea los `PUBLIC_*` y publica cada uno como GitHub Environment
   Variable (`gh variable set ... --env <env>`). Idempotente. Hermetico
   por las reglas de [env-files.md](../../../.claude/rules/env-files.md):
   ningun valor llega a stdout.
2. **`deploy-apps.yml` consume Environment Variables**: el job de
   build/deploy declara `environment: ${{ stage }}`, y cada `env:` del
   step lee `vars.PUBLIC_API_ENDPOINT`, `vars.BASE_DOMAIN`, etc. del
   environment activo. Las vars derivables (`SITE_URL` por niche,
   `BASE_SCHEME=https`) se calculan inline. Se elimina el artifact
   reuse desde `ci.yml`.
3. **Limpieza de docs**: `cloudflare/pages-config.md` se actualiza
   (deja de hablar de git-native; documenta que las vars vienen de GH
   Environments). Se agrega rule corta sobre el flow de client env.

### Decisiones clave

**Decision 1: GitHub Environments con Variables (no Secrets) — por que.**
Las `PUBLIC_*` son publicas por contrato: acaban en el bundle JS del
browser. Marcarlas como Secrets las mascarea en logs (`***`), lo que
estorba el debug del deploy. GH Variables son lo correcto. Las
verdaderas secrets (Turnstile secret key, Neon URL) ya viven en SSM
AWS — fuera del scope.

**Decision 2: 1 widget Turnstile por env (3 sitekeys distintos) — por que.**
Confirmado por el usuario y por
[docker/env/client/.example:31-44](../../../docker/env/client/.example#L31-L44).
El sitekey debe emparejar con el secret en SSM
`/portfolio/{stage}/turnstile-secret`; si no emparejan,
`siteverify` devuelve `invalid-input-secret`. Cada env tiene su widget
con su propia allowlist de hostnames.

**Decision 3: Drop del artifact reuse en CI -> deploy-apps — por que.**
`ci.yml` corre en PRs y en pushes a 3 branches; no conoce el env
destino. Hacer CI env-aware (set vars segun `github.ref_name`)
complica la cache y duplica logica. Mas simple: `deploy-apps.yml`
siempre rebuildea con las vars del env. Costo: ~45s de build con cache
de pnpm. Beneficio: una sola fuente de truth para el build deployable.

**Decision 4: `BASE_DOMAIN`/`APEX_DOMAIN` van como GH Environment
Variables (no hardcoded en workflow) — por que.** Aunque son derivables
del nombre del env, hardcodearlas en el workflow las acopla al cambio
de hostname. Si el portfolio migra a otro dominio, hay que tocar el
yaml. Centralizar en GH Environments (poblado por el script) deja
todo el catalogo de env vars en un solo lugar reproducible.

**Decision 5: `SITE_URL` por matrix item se calcula en el workflow —
por que.** `SITE_URL` depende del niche (no es global del env). En vez
de poner 18 vars (`SITE_URL_GENERIC_DEV`, ...), el workflow lo calcula:
`https://${niche}.${BASE_DOMAIN}` para los 5 niches +
`https://${APEX_DOMAIN}` para generic en prod (o `https://${BASE_DOMAIN}`
en dev/stage donde generic NO tiene apex propio).

### Constraints considerados

- **Build time, no runtime**: Astro es estatico. Las vars deben estar
  presentes en `pnpm build`, no en el deploy. Esto descarta opciones
  tipo Cloudflare Pages Functions o D1 binding.
- **Sin secretos en logs**: PUBLIC_* es OK que aparezca en logs (es
  publica). Secretos NO entran en este plan.
- **Idempotencia del sync**: ejecutar `github_sync` varias veces no debe
  fallar ni cambiar nada si los valores son iguales. Compara antes de
  publicar.
- **Compatibilidad con builds locales sin Docker**: `pnpm run build` sin
  Docker debe seguir funcionando (defaults a prod). El plan NO cambia
  el comportamiento local — solo el deploy.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given push a `dev`, When `deploy-apps.yml` completa, Then
  el HTML de `https://fintech.portfolio.dev.the-full-stack.com/`
  contiene `<div id="cf-tracking-pixel" ... data-api-endpoint="https://api.portfolio.dev.the-full-stack.com">`.
- **AC-2**: Given push a `dev`, When `deploy-apps.yml` completa, Then
  el dropdown "Otras vistas" de cualquier app dev tiene `href`s a
  `*.portfolio.dev.the-full-stack.com` (no a `*.portfolio.the-full-stack.com`).
- **AC-3**: Given push a `dev`, When `deploy-apps.yml` completa, Then
  `<link rel="canonical">` y `<meta property="og:url">` apuntan a
  `*.portfolio.dev.the-full-stack.com`.
- **AC-4**: Given `docker/env/client/.dev` existe con `PUBLIC_API_ENDPOINT=https://...`,
  When ejecuto `python devtools/run.py github_sync --env=dev`, Then
  `gh variable list --env dev` muestra la key con el mismo valor.
- **AC-5**: Given las GH Environment Variables ya estan sincronizadas,
  When ejecuto `python devtools/run.py github_sync --env=dev` por
  segunda vez, Then el script reporta `SKIP` (idempotencia) y no hace
  `gh variable set`.
- **AC-6**: Given un valor de `.dev` cambia, When ejecuto el sync, Then
  reporta `PUSH` y actualiza la GH Variable. La salida del script NO
  contiene el valor (solo el nombre de la key + accion).
- **AC-7**: Given el script falla (ej. `gh` no autenticado), When se
  ejecuta, Then sale con exit code distinto de 0 y un mensaje
  descriptivo SIN el valor del secreto.
- **AC-8**: Given push a `stage`, When `deploy-apps.yml` completa, Then
  Turnstile en `/contact` valida correctamente (sitekey stage emparejado
  con secret SSM stage; submit del form responde 2xx).
- **AC-9**: Given el plan termina, When corro la bateria de
  verificacion E2E (07-verificacion-e2e.md), Then todos los curl
  esperados pasan y `pnpm exec biome check .` + `pnpm run build` + tests
  de devtools pasan en verde.
