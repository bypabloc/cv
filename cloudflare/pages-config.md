# Cloudflare Pages — Configuración de proyectos

> 12 proyectos Cloudflare Pages: 6 apps x 2 ambientes (prod / dev).
> **Deploy via GitHub Actions + wrangler** ([.github/workflows/deploy-apps.yml](../.github/workflows/deploy-apps.yml)).
> Los proyectos Pages NO construyen desde el repo (git-native deprecado para este flujo) — solo aceptan deploys via API con el dist pre-construido.

## Tabla de proyectos

### Producción (branch `main`)

| App | CF Project | Production URL | Dist path |
| --- | --- | --- | --- |
| `apps/generic` | `generic` | `the-full-stack.com` (+ `www`) | `apps/generic/dist` |
| `apps/hub` | `hub` | `hub.portfolio.the-full-stack.com` | `apps/hub/dist` |
| `apps/fintech` | `fintech` | `fintech.portfolio.the-full-stack.com` | `apps/fintech/dist` |
| `apps/architect` | `architect` | `architect.portfolio.the-full-stack.com` | `apps/architect/dist` |
| `apps/leader` | `leader` | `leader.portfolio.the-full-stack.com` | `apps/leader/dist` |
| `apps/vibe` | `vibe` | `vibe.portfolio.the-full-stack.com` | `apps/vibe/dist` |

`portfolio.the-full-stack.com` existe como CNAME que redirige 301 al apex.

### Dev (branch `dev`)

Mismos 6 proyectos con sufijo `-dev`:

| Project | Production URL |
| --- | --- |
| `<app>-dev` | `[<niche>.]portfolio.dev.the-full-stack.com` |

El apex de dev es `portfolio.dev.the-full-stack.com` (= generic).

## Deploy flow (GitHub Actions + wrangler)

```text
push a dev | main
  -> .github/workflows/deploy-apps.yml
     -> resolve-env: branch -> stage + suffix
     -> build-apps (environment: <stage>): pnpm build con env vars del GH Environment
     -> deploy-pages (matrix x6): wrangler pages deploy apps/<niche>/dist
     -> verify-deploy (matrix x6): curl + grep verifica el dist desplegado
     -> report: commit comment con URLs canonicas
```

Las 6 apps comparten un solo build (NO se buildea por niche aparte; `pnpm
-r --filter "./apps/*"` corre las 6 builds en paralelo con las mismas
env vars). Cada deploy del matrix solo necesita su `apps/<niche>/dist`.

## Variables de entorno por env (GitHub Environment Variables)

Las env vars que `site-urls.ts` lee en build time viven como **GitHub
Environment Variables** (NO Secrets — son publicas por contrato `PUBLIC_*`
o config de build derivada). Pobladas por:

```bash
python devtools/run.py sync_secrets --env=dev --category=client   # o prod
```

| Env var | prod | dev |
| --- | --- | --- |
| `BASE_DOMAIN` | `portfolio.the-full-stack.com` | `portfolio.dev.the-full-stack.com` |
| `APEX_DOMAIN` | `the-full-stack.com` | (vacio) |
| `BASE_SCHEME` | `https` | `https` |
| `PUBLIC_API_ENDPOINT` | `https://api.portfolio.the-full-stack.com` | `https://api.portfolio.dev.the-full-stack.com` |
| `PUBLIC_TURNSTILE_SITEKEY` | sitekey prod | sitekey dev |

`APEX_DOMAIN` solo se setea en prod: ahi el apex de generic
(`the-full-stack.com`) difiere del dominio de los niches
(`portfolio.the-full-stack.com`). En dev el apex del env coincide
con `BASE_DOMAIN`, asi que `APEX_DOMAIN` no se necesita.

`SITE_URL` ya **NO** se necesita por niche: cada `apps/*/astro.config.ts`
deriva su SITE de `buildSiteUrl('<niche>')` cuando `process.env.SITE_URL`
no esta seteada. Asi una sola tabla de vars cubre las 6 apps.

Fuente de los valores: `docker/env/client/.{env}` (gitignored). El
script `sync_secrets --category=client` lee y publica idempotentemente.
Comando unificado para las 3 categorias (`client` / `server` / `dev-cli`):
ver [.claude/rules/secrets-strategy.md](../.claude/rules/secrets-strategy.md).

## Headers de seguridad

Cada app sirve un `_headers` con:

```text
/*
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'
  X-Frame-Options: DENY
```

> Nota: `script-src 'unsafe-inline'` es necesario por el script inline anti-FOUC del BaseLayout.

## Verificación post-deploy

```bash
# prod
curl -sI https://fintech.portfolio.the-full-stack.com/ | grep -i 'strict-transport'
curl -s https://fintech.portfolio.the-full-stack.com/llms.txt | head -5
# dev
curl -sI https://fintech.portfolio.dev.the-full-stack.com/
curl -sI https://fintech.portfolio.dev.the-full-stack.com/
```

## Rollback

Cloudflare Pages mantiene los últimos N deploys. En el dashboard del proyecto:

1. `Deployments` tab
2. Seleccionar deployment anterior estable
3. `Rollback to this deployment`
