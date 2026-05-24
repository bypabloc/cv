# Spec: build env vars per env (deploy-apps + github sync)

> Las 6 apps Astro se deployan a Cloudflare Pages dev/stage/prod sin que el
> build reciba las env vars del entorno destino. Resultado: todas las URLs y el
> endpoint del API se hornean con defaults de produccion. Este plan inyecta
> las env vars correctas por entorno y crea un script de sync para
> `docker/env/client/.{env}` -> GitHub Environments.

## Estado

| Fase | Estado | Archivos |
|------|--------|----------|
| 1 — Regression guards (3 capas: A guard, B build-test, C smoke) | pending | `packages/app-shared/`, `packages/ui/`, `deploy-apps.yml` |
| 2 — Script `github_sync` en devtools | pending | `devtools/github_sync/` |
| 3 — `deploy-apps.yml` consume Environment Variables | pending | `.github/workflows/deploy-apps.yml`, `ci.yml`, 6 `astro.config.ts` |
| 4 — Limpieza de docs obsoletas | pending | `cloudflare/pages-config.md`, `.claude/rules/` |
| 5 — Verificacion E2E | pending | (sin codigo) |

## Cuando leer

| Archivo | Cuando |
|---------|--------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Entender por que las URLs del dropdown / `/track` apuntan a prod en dev |
| [02-fase-1-regression-guards.md](02-fase-1-regression-guards.md) | Cerrar el hueco que dejo pasar el bug (build guard + build test + smoke test) |
| [03-fase-2-github-sync.md](03-fase-2-github-sync.md) | Crear el script `python devtools/run.py github_sync --env=<X>` |
| [04-fase-3-deploy-workflow.md](04-fase-3-deploy-workflow.md) | Modificar `deploy-apps.yml` + `ci.yml` para inyectar vars al build |
| [05-fase-4-cleanup-docs.md](05-fase-4-cleanup-docs.md) | Actualizar `pages-config.md`, agregar rule `client-env-sync` |
| [06-commits.md](06-commits.md) | 12 commits incrementales (cada uno deja el repo verde) |
| [07-paralelizacion-worktrees.md](07-paralelizacion-worktrees.md) | Donde se puede paralelizar con git worktrees y donde no |
| [08-verificacion-e2e.md](08-verificacion-e2e.md) | Bateria de cierre: 11 comandos en bucle hasta verde + PR |

## Decisiones no-reabribles

1. **GitHub Environments con Variables (no Secrets)**: las `PUBLIC_*`
   son publicas (acaban en el bundle). Se pueden ver en logs sin riesgo.
   Se usa `gh variable set ... --env <env>`, no `gh secret set`. Solo
   `TURNSTILE_SECRET_KEY` y similares iran como Secrets (ya viven en SSM
   AWS, fuera del scope de este plan).
2. **1 widget Turnstile por env**: confirmado por el usuario y por
   [docker/env/client/.example:31](../../../docker/env/client/.example#L31).
   `PUBLIC_TURNSTILE_SITEKEY` difiere en dev/stage/prod.
3. **Drop del artifact reuse en CI -> deploy-apps**: `ci.yml` no conoce el
   env destino (corre en PRs y en pushes a 3 branches). Hacer el build
   env-aware en CI complica la cache; mas simple: `deploy-apps.yml`
   siempre rebuildea con las vars del env. El build tarda ~45s con cache
   de pnpm — costo aceptable.
4. **Script `github_sync` lee `docker/env/client/.{env}`**: la fuente de
   verdad del valor sigue siendo local (gitignored). El script publica
   cada `PUBLIC_*` como GitHub Environment Variable via `gh variable set`.
   Idempotente (compara antes de publicar). Hermetico (no imprime valores).
5. **`SITE_URL` por niche+env se calcula en el workflow**: NO va en
   `docker/env/client/.{env}`. Lo deriva la matrix de `deploy-apps.yml`
   con `https://${niche}.${BASE_DOMAIN}` (o el apex para generic en prod).

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** las env vars `PUBLIC_*` se setean en `env:` del job de
  build, ANTES del `pnpm ... build`. Astro las hornea via
  `import.meta.env.*` en build time — setearlas en deploy es tarde.
- **SIEMPRE** el script `github_sync` cumple [env-files.md](../../../.claude/rules/env-files.md):
  no imprime valores, no copia el `.env` al contexto, extrae cada KEY
  con `grep -m1 ^KEY=` o equivalente Python sin volcar el archivo.
- **NUNCA** marcar las `PUBLIC_*` como GitHub Secrets — distorsiona la
  semantica (los Secrets se mascarean en logs, las Variables no) y
  rompe la visibilidad post-deploy. Son publicas por contrato.
- **NUNCA** hardcodear el sitekey de Turnstile en `deploy-apps.yml` —
  cambia cuando se rota el widget. Va via GH Environment Variables.

## Mapping branch -> env -> URLs (canonico)

| branch | stage | `BASE_DOMAIN` | `APEX_DOMAIN` | `PUBLIC_API_ENDPOINT` |
|--------|-------|---------------|---------------|------------------------|
| `dev` | dev | `portfolio.dev.the-full-stack.com` | (vacio) | `https://api.portfolio.dev.the-full-stack.com` |
| `stage` | stage | `portfolio.stage.the-full-stack.com` | (vacio) | `https://api.portfolio.stage.the-full-stack.com` |
| `main` | prod | `portfolio.the-full-stack.com` | `the-full-stack.com` | `https://api.portfolio.the-full-stack.com` |

`BASE_SCHEME=https` en los 3.

`SITE_URL` por matrix item:
- generic + prod: `https://the-full-stack.com` (apex)
- otros: `https://${niche}.${BASE_DOMAIN}` o `https://${niche}.${APEX_DOMAIN}` segun corresponda

## Matriz de verificacion

| Sintoma actual | Verificacion post-fix |
|----------------|------------------------|
| Dropdown "Otras vistas" linkea a prod | `curl https://fintech.portfolio.dev.the-full-stack.com/` → hrefs `*.portfolio.dev.*` |
| `cf-tracking-pixel` sin `data-api-endpoint` | `curl ... \| grep cf-tracking-pixel` → contiene `data-api-endpoint="https://api.portfolio.dev..."` |
| Canonical/OG = prod en dev | `curl ... \| grep og:url` → `portfolio.dev.the-full-stack.com` |
| `/track` no se ejecuta | DevTools Network: POST a `api.portfolio.dev...` en page load |
| `/contact` Turnstile invalido | Form submit OK con widget dev (sitekey emparejado con secret SSM dev) |

## Referencias cruzadas

- [.claude/rules/plan-format.md](../../../.claude/rules/plan-format.md) — formato de este plan
- [.claude/rules/env-files.md](../../../.claude/rules/env-files.md) — politica de no-lectura de .env
- [.claude/rules/ci-cd-pipeline.md](../../../.claude/rules/ci-cd-pipeline.md) — workflows del repo
- [packages/app-shared/src/lib/site-urls.ts](../../../packages/app-shared/src/lib/site-urls.ts) — consumidor de `BASE_DOMAIN`/`APEX_DOMAIN`
- [packages/ui/src/components/TrackingPixel.astro](../../../packages/ui/src/components/TrackingPixel.astro) — consumidor de `PUBLIC_API_ENDPOINT`
- [cloudflare/pages-config.md](../../../cloudflare/pages-config.md) — doc actual (a actualizar en Fase 3)
