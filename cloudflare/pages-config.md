# Cloudflare Pages — Configuración de proyectos

> 6 proyectos Cloudflare Pages, uno por app. Cada uno con su dominio asignado.

## Tabla de proyectos

| App | CF Project name | Production URL | Dist path |
|-----|-----------------|----------------|-----------|
| `apps/hub` | `portfolio-hub` | `the-full-stack.com` | `apps/hub/dist` |
| `apps/generic` | `portfolio-generic` | `hub.the-full-stack.com` | `apps/generic/dist` |
| `apps/fintech` | `portfolio-fintech` | `fintech.the-full-stack.com` | `apps/fintech/dist` |
| `apps/architect` | `portfolio-architect` | `architect.the-full-stack.com` | `apps/architect/dist` |
| `apps/leader` | `portfolio-leader` | `leader.the-full-stack.com` | `apps/leader/dist` |
| `apps/vibe` | `portfolio-vibe` | `vibe.the-full-stack.com` | `apps/vibe/dist` |

## Setup manual (una sola vez)

1. **Login en Cloudflare Dashboard** → `Pages → Create a project → Direct Upload`.
2. Crear los 6 proyectos con los nombres de la tabla. **No** conectar a Git desde Cloudflare; GitHub Actions hace el deploy.
3. **Asignar dominios** en cada proyecto:
   - `portfolio-hub` → custom domain `the-full-stack.com` (root)
   - `portfolio-generic` → custom domain `hub.the-full-stack.com`
   - `portfolio-fintech` → custom domain `fintech.the-full-stack.com`
   - (idem para architect, leader, vibe)
4. **Generar API token** con permiso `Cloudflare Pages — Edit`:
   - User profile → API Tokens → Create custom token
   - Permissions: `Account · Cloudflare Pages · Edit`, `Zone · DNS · Read`
   - Account resources: Include - your account
   - Zone resources: Include - the-full-stack.com
5. **Agregar secrets en GitHub** (`Settings → Secrets and variables → Actions`):
   - `CLOUDFLARE_API_TOKEN` — el token del paso 4
   - `CLOUDFLARE_ACCOUNT_ID` — Account ID del dashboard

## Headers de seguridad

Cada app sirve un `_headers` con:

```
/*
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'
  X-Frame-Options: DENY
```

> Nota: `script-src 'unsafe-inline'` es necesario por el script inline anti-FOUC del BaseLayout. Si querés CSP estricto sin `'unsafe-inline'`, mover ese script a un archivo separado e incluir el hash en CSP.

## Deploy

GitHub Actions `deploy.yml` se dispara en push a `main`:

- Solo se rebuilda lo que cambió (path filtering por carpeta `apps/<app>/`).
- Si cambia un `packages/*`, se rebuilda **todo** (broadcast).
- Manual: usar workflow_dispatch en GitHub UI con app específica.

## Variables de entorno por app (CF Pages)

Cada proyecto puede definir `SITE_URL` para reescribir la canonical (útil si el dominio cambia):

| Project | Env var | Value |
|---------|---------|-------|
| `portfolio-hub` | `SITE_URL` | `https://the-full-stack.com` |
| `portfolio-generic` | `SITE_URL` | `https://hub.the-full-stack.com` |
| ... | ... | ... |

## Verificación post-deploy

```bash
# Reemplazar <subdomain> por hub/fintech/architect/leader/vibe
curl -sI https://<subdomain>.the-full-stack.com/ | grep -i 'content-security\|strict-transport'
curl -s https://<subdomain>.the-full-stack.com/llms.txt | head -5
curl -s https://<subdomain>.the-full-stack.com/robots.txt
curl -s https://<subdomain>.the-full-stack.com/sitemap-index.xml | head -5
```

## Rollback

Cloudflare Pages mantiene los últimos N deploys. En el dashboard del proyecto:

1. `Deployments` tab
2. Seleccionar deployment anterior estable
3. `Rollback to this deployment`
