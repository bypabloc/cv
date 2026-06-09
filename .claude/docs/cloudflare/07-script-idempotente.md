# Script idempotente: `devtools/cloudflare_setup/`

> Como esta organizado el script Python que gestiona todo el setup,
> que fases tiene, y como usarlo. Soporta los 12 Pages projects del
> portfolio (6 niches x 2 envs) via `--env=dev|prod`.

[← Gotchas](./06-gotchas.md) | [README](./README.md) | [Siguiente: Comparacion proveedores →](./08-vercel-netlify-vs-cloudflare.md)

## Por que un script Python

- **Devtools** del portfolio ya usa Python 3.14 + uv
- **Idempotente**: re-correr no rompe (chequea state antes de mutar)
- **Reproducible**: agrega una app nueva → tocar `config.py` → re-correr
- **Multi-env**: la misma fase opera contra dev/prod con
  `--env=<env>` (default `prod`); no hay codigo duplicado por env
- **Sin dependencia en wrangler**: la REST API directa cubre todo el
  flow (wrangler no soporta git-connected creation)
- **Documentado**: cada decision tiene comentarios in-code

## Estructura

```
devtools/cloudflare_setup/
├── __init__.py
├── config.py      # APPS (niche-level) + ENVS (env-level) + helpers
├── payloads.py    # JSON shapes parametrizados por (app, env_cfg)
├── api.py         # Cliente httpx (sync) con CloudflareError
├── flags.py       # CLI: phase posicional + --env=<X>
├── main.py        # Orquestador con fases idempotentes
└── README.md      # Referencia operativa del script
```

### `config.py`

Define `APPS: tuple[AppConfig, ...]` y `ENVS: dict[str, EnvConfig]`. La
combinacion `APPS x ENVS` da los 12 Pages projects.

`AppConfig` (niche-level, env-agnostic):

| Campo | Significado |
|-------|-------------|
| `project_name` | Identificador del niche (= Pages project name en prod) |
| `package_name` | Nombre pnpm del workspace (e.g. `@portfolio/generic`) |
| `root_dir` | Path relativo desde repo root (`apps/generic`) |

`EnvConfig` (env-level):

| Campo | Significado |
|-------|-------------|
| `env` | `'dev'` \| `'prod'` |
| `branch` | Branch GitHub que Pages construye (`main`/`dev`) |
| `base_domain` | FQDN al que cuelgan los niches |
| `apex_domain` | Solo prod (`the-full-stack.com`); `None` en dev |
| `api_endpoint` | URL del backend API (`https://api.<base_domain>`) |
| `turnstile_sitekey` | Public sitekey del widget Cloudflare Turnstile (1 por env) |

Helpers que derivan los valores per (app, env):

- `project_name_for(app, env)` — `generic` (prod) | `generic-dev`
- `custom_domain_for(app, env_cfg)` — apex en prod-generic, sino subdominio
- `site_url_for(app, env_cfg)` — `https://<custom_domain>`

`GLOBAL_ENV_VARS` lleva las constantes globales (`NODE_VERSION=24`,
`PNPM_VERSION=11.0.9`, `BASE_SCHEME=https`). El resto de env vars
(`BASE_DOMAIN`, `APEX_DOMAIN`, `PUBLIC_API_ENDPOINT`,
`PUBLIC_TURNSTILE_SITEKEY`, `SITE_URL`) se derivan en
`payloads._env_vars(app, env_cfg)`.

### `payloads.py`

Centraliza las JSON shapes, parametrizadas por `(app, env_cfg)`:

- `build_create_project_payload(app, env_cfg)` — body del POST, incluye
  `production_branch`, `preview_branch_includes=[env_cfg.branch]` (lock
  por branch, ver memoria `cloudflare-pages-preview-branch-fix`).
- `build_patch_project_payload(app, env_cfg)` — body del PATCH; reescribe
  `build_config` + `env_vars` (config-as-truth: cambios manuales en la
  consola Cloudflare se revierten al re-correr).

### `api.py`

`CloudflareClient` con metodos:

- `get_project(name)` / `create_project(payload)` / `patch_project(name, payload)` / `delete_project(name)`
- `list_domains(project)` / `attach_domain(project, domain)`
- `list_deployments(project)` / `trigger_deployment(project)`
- `list_dns_records(zone_id, name=...)` / `create_dns_record(zone_id, ...)`
- `get_zone_id(zone_name)`

Cada metodo unwrappea el envelope `{success, result, errors}` y levanta
`CloudflareError` si `success=false`. Soporta `allow_404=True` para
`get_project` (idempotency).

### `flags.py`

Integra el script al CLI `devtools/run.py` con `flag()` + `describe()`.
Parsea `phase` posicional (default `all`) y `--env=<X>` (default `prod`).
Valida contra `VALID_PHASES` y `VALID_ENVS`.

### `main.py`

Orquestador. Cada fase recibe `env_cfg` y resuelve `project_name`,
`custom_domain` per env via los helpers de `config.py`:

```python
def phase_projects(client, env_cfg):
    for app in APPS:
        name = project_name_for(app, env_cfg.env)
        existing = client.get_project(name)
        if existing is None:
            client.create_project(build_create_project_payload(app, env_cfg))
        else:
            client.patch_project(name, build_patch_project_payload(app, env_cfg))
```

## Fases disponibles

```bash
python devtools/run.py cloudflare_setup <phase> [--env=<env>]
```

`<env>` por defecto es `prod`. Para dev agregar `--env=dev`.

| Phase | Que hace | Idempotente? |
|-------|----------|--------------|
| `projects` | Crea o patchea los 6 proyectos del env | si (create si no existe, patch si existe) |
| `domains` | Attacha custom domains del env a sus proyectos | si (skip si ya attached) |
| `dns` | Crea/actualiza CNAMEs en la zona apuntando al `<project>.pages.dev` real | si (PUT replaces si target cambio) |
| `status` | Imprime ultimo deployment por proyecto del env | si (read-only) |
| `trigger` | Trigger deploy manual de cada proyecto del env | NO (cada llamada crea un build nuevo) |
| `all` | Corre projects → domains → dns → status | si |

## Credenciales

`run.py` NO auto-carga `tmp/cloudflare-creds.env`. Exportar antes o
pasar inline:

```bash
# Exportar
set -a; . tmp/cloudflare-creds.env; set +a
python devtools/run.py cloudflare_setup status --env=dev

# Inline (preferido para invocaciones puntuales)
CLOUDFLARE_API_TOKEN="$(grep -m1 '^CLOUDFLARE_API_TOKEN=' tmp/cloudflare-creds.env | cut -d= -f2-)" \
ACCOUNT_ID="$(grep -m1 '^ACCOUNT_ID=' tmp/cloudflare-creds.env | cut -d= -f2-)" \
  python devtools/run.py cloudflare_setup status --env=dev
```

Contenido del file (gitignored):
```
CLOUDFLARE_API_TOKEN=v1.0_xxx...
ACCOUNT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Template (commiteado): `tmp/cloudflare-creds.env.template`.

Politica de extraccion: NUNCA volcar el `.env` completo. Ver
`.claude/rules/env-files.md`.

## Agregar una app nueva al setup

1. Crear `apps/<app-nueva>/` con su `package.json`, schema Astro, etc.
2. Editar `devtools/cloudflare_setup/config.py`:
   ```python
   APPS = (
       # ... apps existentes ...
       AppConfig(
           project_name='nueva',
           package_name='@portfolio/nueva',
           root_dir='apps/nueva',
       ),
   )
   ```
3. Cargar credenciales y correr (2 envs = 2 invocaciones):
   ```bash
   set -a; . tmp/cloudflare-creds.env; set +a
   for env in prod dev; do
     python devtools/run.py cloudflare_setup all --env=$env
   done
   ```

El script para cada env:

- Crea el proyecto `nueva` / `nueva-dev` (skip los
  existentes)
- Attacha el domain derivado per env (apex/subdomain) (skip los
  existentes)
- Crea el CNAME apuntando al subdomain real del proyecto nuevo
- Imprime status

## Agregar un env nuevo

Si en el futuro se agrega `qa` o similar:

1. Crear la branch GitHub.
2. Agregar entrada a `ENVS` en `config.py`:
   ```python
   ENVS = {
       # ... envs existentes ...
       'qa': EnvConfig(
           env='qa',
           branch='qa',
           base_domain=f'portfolio.qa.{APEX_DOMAIN}',
           apex_domain=None,
           api_endpoint=f'https://api.portfolio.qa.{APEX_DOMAIN}',
           turnstile_sitekey='0x...',
       ),
   }
   ```
3. Crear el widget Turnstile correspondiente (skill `rotate-secrets`).
4. `python devtools/run.py cloudflare_setup all --env=qa` provisiona
   los 6 projects nuevos del env, los domains y los CNAMEs.

## Troubleshoot

### "non-JSON response (HTTP 304)"

Trigger de deploy del mismo commit. Hacer commit nuevo o usar
`--allow-empty`. Ver [06-gotchas.md](./06-gotchas.md#3).

### "POST /pages/projects → success=false"

Inspeccionar `errors[]` del response. Tipico:

- `8000007: Project name already exists` → ya existe; phase `projects`
  deberia haber patcheado en vez de crear
- `8000045: Source repository not connected` → la GitHub App de
  Cloudflare no esta autorizada para `bypabloc/cv`. Solucion:
  https://dash.cloudflare.com → Workers & Pages → Create →
  Pages → Connect to Git → autorizar GitHub App

### "Cannot find zone the-full-stack.com"

Token no tiene `Zone DNS Read/Edit` o el dominio no esta en CF DNS.
Verificar con:
```bash
curl -s "https://api.cloudflare.com/client/v4/zones?name=the-full-stack.com" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

### "env invalido: 'local'"

Solo `dev|prod` son envs soportados. No hay `local` (eso es
Docker, ver `python devtools/run.py docker up --env=local`).

## Verificacion

```bash
# Unit tests del modulo (64 tests)
python devtools/run.py test_runner --module=devtools --type=unit -- \
  devtools/tests/unit/src/cloudflare_setup/

# Ruff
devtools/.venv/bin/python -m ruff check devtools/cloudflare_setup/

# Smoke contra Cloudflare real (read-only)
CLOUDFLARE_API_TOKEN=... ACCOUNT_ID=... \
  python devtools/run.py cloudflare_setup status --env=prod
```

El modulo respeta el ruff config de `devtools/ruff.toml` (Python 3.14,
line-length 80, single quotes para tecnicos).
