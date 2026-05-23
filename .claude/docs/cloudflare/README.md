# Cloudflare deployment knowledge base

> Conocimiento consolidado sobre como esta desplegado este portfolio en
> Cloudflare Pages y como gestionar el setup via API token. Cada nodo
> cubre un tema; navegar por relevancia, no leer linealmente.

## Cuando leer cada archivo

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Arquitectura global del deploy | [01-architecture.md](./01-architecture.md) | Entender que son los 6 proyectos Pages + DNS + custom domains |
| API token: permisos y manejo | [02-api-token.md](./02-api-token.md) | Crear, rotar, revocar token con permisos minimos |
| Setup via REST API (Pages projects) | [03-pages-api-setup.md](./03-pages-api-setup.md) | Crear proyectos Pages git-connected programaticamente |
| Build config para monorepo pnpm | [04-monorepo-build-config.md](./04-monorepo-build-config.md) | Build command + root_dir + destination_dir correctos |
| DNS records y CNAME flattening | [05-dns-and-custom-domains.md](./05-dns-and-custom-domains.md) | Apex con CNAME, subdomain real con sufijo aleatorio |
| Gotchas conocidos | [06-gotchas.md](./06-gotchas.md) | Errores tipicos: Cannot find cwd, 403 cert pending, DNS cache |
| Script idempotente del proyecto | [07-script-idempotente.md](./07-script-idempotente.md) | devtools/cloudflare_setup/ — 18 projects (6 niches x 3 envs via `--env=<X>`), fases, comandos, troubleshoot |
| Comparacion con alternativas | [08-vercel-netlify-vs-cloudflare.md](./08-vercel-netlify-vs-cloudflare.md) | Por que Cloudflare Pages para este portfolio |
| Workers Static Assets (futuro) | [09-workers-static-assets-future.md](./09-workers-static-assets-future.md) | Cuando migrar de Pages a Workers |

## Reglas criticas

- NUNCA dar al API token permisos mas alla de los necesarios. Permisos
  minimos en [02-api-token.md](./02-api-token.md).
- NUNCA commitear `tmp/cloudflare-creds.env`. Esta en `.gitignore`.
- NUNCA usar `npx wrangler deploy` para git-connected — wrangler solo
  soporta direct upload, los proyectos git-connected se crean via REST
  API (ver [03-pages-api-setup.md](./03-pages-api-setup.md)).
- SIEMPRE resolver el subdomain real del proyecto Pages antes de crear
  el CNAME (CF agrega sufijo aleatorio si el nombre esta tomado).
  Detalle en [05-dns-and-custom-domains.md](./05-dns-and-custom-domains.md).
- SIEMPRE rotar/revocar el token cuando termina la tarea. Detalle en
  [02-api-token.md](./02-api-token.md).

## Quick start: re-deployar todo

```bash
# 1. Crear token (ver 02-api-token.md), guardar en tmp/cloudflare-creds.env
cp tmp/cloudflare-creds.env.template tmp/cloudflare-creds.env
# editar y completar CLOUDFLARE_API_TOKEN + ACCOUNT_ID

# 2. Correr script idempotente (default --env=prod; pasar --env=dev|stage para otros)
set -a; . tmp/cloudflare-creds.env; set +a
python devtools/run.py cloudflare_setup all --env=prod

# 3. Verificar
python devtools/run.py cloudflare_setup status --env=prod

# 4. Limpiar
rm -f tmp/cloudflare-creds.env
# revocar token en dashboard: https://dash.cloudflare.com/profile/api-tokens
```

Para dev/stage:

```bash
python devtools/run.py cloudflare_setup status  --env=dev      # los 6 *-dev
python devtools/run.py cloudflare_setup trigger --env=stage    # rebuild *-stage sin push
python devtools/run.py cloudflare_setup all     --env=dev      # reconciliacion full dev
```

## Estado actual del deploy (2026-05-23)

- 18 proyectos Pages: 6 niches x 3 envs (prod sin sufijo, dev y stage
  con sufijo `-dev`/`-stage`)
  - Prod: `generic`, `hub`, `fintech`, `architect`, `leader`, `vibe`
  - Dev: `generic-dev`, `hub-dev`, `fintech-dev`, `architect-dev`, `leader-dev`, `vibe-dev`
  - Stage: `generic-stage`, `hub-stage`, `fintech-stage`, `architect-stage`, `leader-stage`, `vibe-stage`
- Dominio: `the-full-stack.com` (apex + www) + 5 subdominios prod;
  `portfolio.dev.the-full-stack.com` + 5 subdominios dev; idem stage
- DNS: zona en Cloudflare DNS (NS = `*.ns.cloudflare.com`)
- Registrar: AWS Route 53 (no requiere migracion)
- SSL: Universal SSL automatico (Google CA via CF)
- Branch -> env: `main` -> prod, `dev` -> dev, `stage` -> stage
  (`preview_branch_includes` lockea cada project a su propia branch)
- Build: `pnpm install --frozen-lockfile && pnpm --filter @portfolio/<app>... build`
- Headers: `_headers` en `apps/*/public/` con CSP estricta + HSTS + X-Frame DENY
