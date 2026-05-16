# Cloudflare Pages — Configuración de proyectos

> 18 proyectos Cloudflare Pages: 6 apps x 3 ambientes (prod / dev / stage).
> Deploy git-native (Cloudflare construye desde el repo, sin GitHub Actions).

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

### Dev (branch `dev`) y Stage (branch `stage`)

Mismos 6 proyectos por env con sufijo `-dev` / `-stage`:

| Project | Production URL |
| --- | --- |
| `<app>-dev` | `[<niche>.]portfolio.dev.the-full-stack.com` |
| `<app>-stage` | `[<niche>.]portfolio.stage.the-full-stack.com` |

El apex de dev/stage es `portfolio.{env}.the-full-stack.com` (= generic).

## Deploy git-native

Cada proyecto está conectado al repo `bypabloc/cv` con su
`production_branch` (`main` / `dev` / `stage`). Cloudflare buildea con:

```text
build_command:   pnpm install --frozen-lockfile && pnpm --filter @portfolio/<app>... build
destination_dir: apps/<app>/dist
root_dir:        (vacio)
```

Un push a la branch correspondiente dispara el build + deploy. No hay
workflow de GitHub Actions para el deploy del frontend.

## Variables de entorno por proyecto (build env vars)

Cada proyecto define las env vars que `site-urls.ts` lee en build time:

| Env var | prod | dev | stage |
| --- | --- | --- | --- |
| `BASE_DOMAIN` | `portfolio.the-full-stack.com` | `portfolio.dev.the-full-stack.com` | `portfolio.stage.the-full-stack.com` |
| `APEX_DOMAIN` | `the-full-stack.com` | (no se setea) | (no se setea) |
| `BASE_SCHEME` | `https` | `https` | `https` |
| `SITE_URL` | hostname propio de la app | idem | idem |
| `NODE_VERSION` | `24` | `24` | `24` |
| `PNPM_VERSION` | `11.0.9` | `11.0.9` | `11.0.9` |

`APEX_DOMAIN` solo se setea en prod: ahi el apex de generic
(`the-full-stack.com`) difiere del dominio de los niches
(`portfolio.the-full-stack.com`). En dev/stage el apex del env coincide
con `BASE_DOMAIN`, asi que `APEX_DOMAIN` no se necesita.

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
# dev / stage
curl -sI https://fintech.portfolio.dev.the-full-stack.com/
curl -sI https://fintech.portfolio.stage.the-full-stack.com/
```

## Rollback

Cloudflare Pages mantiene los últimos N deploys. En el dashboard del proyecto:

1. `Deployments` tab
2. Seleccionar deployment anterior estable
3. `Rollback to this deployment`
