# cloudflare_setup

Orquestador idempotente de los 14 proyectos Cloudflare Pages del portfolio
(7 apps x 2 envs). Cada fase chequea estado actual antes de mutar, asi
que se puede re-correr sin riesgo.

## Uso

```bash
python devtools/run.py cloudflare_setup <phase> [--env=<env>]
```

- `phase` (posicional, default `all`): que fase ejecutar.
- `--env=dev|prod` (default `prod`): entorno objetivo.

## Fases

| Fase | Que hace |
| --- | --- |
| `projects` | Crea o patchea los 6 Pages projects del env (build_config + env_vars). |
| `domains` | Adjunta el custom domain (apex/subdominio) a cada project. |
| `dns` | Crea/actualiza records CNAME en Cloudflare DNS apuntando a `<project>.pages.dev`. |
| `status` | Imprime el ultimo deployment de cada project. |
| `trigger` | Dispara un build fresco en cada project (sin push a GitHub). |
| `all` | `projects -> domains -> dns -> status` en orden. |

## Modelo: project_name + branch + custom_domain por env

Los 14 projects se derivan de `APPS` x `ENVS` en `config.py`:

| Niche x Env | project_name | branch | custom_domain |
| --- | --- | --- | --- |
| generic / prod | `generic` | `main` | `the-full-stack.com` (apex) |
| generic / dev | `generic-dev` | `dev` | `portfolio.dev.the-full-stack.com` |
| `<niche>` / prod | `<niche>` | `main` | `<niche>.portfolio.the-full-stack.com` |
| `<niche>` / dev | `<niche>-dev` | `dev` | `<niche>.portfolio.dev.the-full-stack.com` |

donde `<niche>` esta en `{hub, fintech, architect, leader, vibe}`.

## Env vars per (app, env)

Las env vars se aplican via patch en cada `projects --env=<X>` (config
es la unica fuente de verdad — cambios manuales en la consola Cloudflare
se revierten). Por env:

| Variable | prod | dev |
| --- | --- | --- |
| `BASE_DOMAIN` | `portfolio.the-full-stack.com` | `portfolio.dev.the-full-stack.com` |
| `APEX_DOMAIN` | `the-full-stack.com` | (ausente) |
| `PUBLIC_API_ENDPOINT` | `https://api.portfolio.the-full-stack.com` | `https://api.portfolio.dev.the-full-stack.com` |
| `PUBLIC_TURNSTILE_SITEKEY` | widget prod | widget dev |
| `SITE_URL` (generic) | `https://the-full-stack.com` | `https://portfolio.dev.the-full-stack.com` |
| `SITE_URL` (`<niche>`) | `https://<niche>.portfolio.the-full-stack.com` | `https://<niche>.portfolio.dev.the-full-stack.com` |

Constantes en todos los envs: `NODE_VERSION=24`, `PNPM_VERSION=11.0.9`,
`BASE_SCHEME=https`.

## Credenciales

`CLOUDFLARE_API_TOKEN` y `ACCOUNT_ID` se leen del environment. `run.py`
NO auto-carga `tmp/cloudflare-creds.env`; exportar antes o pasar inline:

```bash
CLOUDFLARE_API_TOKEN="$(grep -m1 '^CLOUDFLARE_API_TOKEN=' tmp/cloudflare-creds.env | cut -d= -f2-)" \
ACCOUNT_ID="$(grep -m1 '^ACCOUNT_ID=' tmp/cloudflare-creds.env | cut -d= -f2-)" \
  python devtools/run.py cloudflare_setup status --env=dev
```

Politica de extraccion de keys: ver `.claude/rules/env-files.md` (NUNCA
volcar el archivo `.env` completo).

## Ejemplos comunes

```bash
# Estado de los 6 *-dev projects
python devtools/run.py cloudflare_setup status --env=dev

# Triggerea rebuild de los 7 *-dev projects (sin push a GitHub)
python devtools/run.py cloudflare_setup trigger --env=dev

# Setup desde cero o reconciliacion total de prod (idempotente)
python devtools/run.py cloudflare_setup all --env=prod

# Idem dev
python devtools/run.py cloudflare_setup all --env=dev

# Solo aplicar env_vars + build_config (no toca domains ni dns)
python devtools/run.py cloudflare_setup projects --env=dev
```

## Idempotencia

- `projects`: GET project; si no existe -> POST create; si existe ->
  PATCH (build_config + env_vars del config.py).
- `domains`: GET domains; si el FQDN ya esta attached -> skip; si no ->
  POST attach.
- `dns`: lista CNAMEs del zone con `name=<custom_domain>`; si existe
  y apunta al `<project>.pages.dev` correcto -> skip; si difiere -> PUT
  in place; si no existe -> POST create.
- `trigger`: NO es idempotente — cada llamada dispara un build nuevo.
- `status`: read-only.

## Verificacion

```bash
# Unit tests del modulo
python devtools/run.py test_runner --module=devtools --type=unit -- \
  devtools/tests/unit/src/cloudflare_setup/

# Ruff
devtools/.venv/bin/python -m ruff check devtools/cloudflare_setup/

# Smoke contra Cloudflare (no muta)
CLOUDFLARE_API_TOKEN=... ACCOUNT_ID=... \
  python devtools/run.py cloudflare_setup status --env=prod
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
| --- | --- | --- |
| Hardcodear `--env=prod` en scripts de operacion | Frente a multi-env, queda invisible que solo afecta prod | Pasar `--env=<env>` explicito siempre |
| Cambiar env_vars en la consola Cloudflare | El siguiente `projects --env=<X>` los revierte | Editar `config.py` (ENVS o `_env_vars`) y correr `projects --env=<X>` |
| Llamar a la API REST de Cloudflare con curl porque "el script no sabe de dev" | Era cierto antes; ya no — el script cubre los 18 projects | Usar `cloudflare_setup <phase> --env=<X>` |
| Olvidar exportar `CLOUDFLARE_API_TOKEN` / `ACCOUNT_ID` | `run.py` no auto-carga `tmp/cloudflare-creds.env` | Exportar o pasar inline (ver ejemplo arriba) |

## Referencias

- Concepto + setup: `.claude/docs/cloudflare/` (skill `cloudflare-deploy`)
- Subdomain pattern: `.claude/docs/subdomain-standard/` (skill `subdomain-standard`)
- Turnstile (widget keys por env): `.claude/skills/rotate-secrets/SKILL.md` +
  `.claude/rules/serverless-secrets.md`
- Convenciones del CLI devtools: `.claude/rules/devtools.md`
