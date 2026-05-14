# Script idempotente: `devtools/cloudflare_setup/`

> Como esta organizado el script Python que gestiona todo el setup,
> que fases tiene, y como usarlo.

[← Gotchas](./06-gotchas.md) | [README](./README.md) | [Siguiente: Comparacion proveedores →](./08-vercel-netlify-vs-cloudflare.md)

## Por que un script Python

- **Devtools** del portfolio ya usa Python 3.14 + uv
- **Idempotente**: re-correr no rompe (chequea state antes de mutar)
- **Reproducible**: agrega una app nueva → tocar `config.py` → re-correr
- **Sin dependencia en wrangler**: la REST API directa cubre todo el
  flow (wrangler no soporta git-connected creation)
- **Documentado**: cada decision tiene comentarios in-code

## Estructura

```
devtools/cloudflare_setup/
├── __init__.py
├── config.py      # Single source of truth: APPS, dominios, env vars
├── payloads.py    # JSON shapes para Cloudflare REST API
├── api.py         # Cliente httpx (sync) con CloudflareError
└── main.py        # Orquestador con fases idempotentes
```

### `config.py`

Define `APPS: tuple[AppConfig, ...]` — la fuente de verdad. Cada
`AppConfig` tiene:

| Campo | Significado |
|-------|-------------|
| `project_name` | Nombre del proyecto en Pages (tambien default subdomain) |
| `package_name` | Nombre pnpm del workspace (e.g. `@portfolio/generic`) |
| `root_dir` | Path relativo desde repo root (`apps/generic`) |
| `custom_domain` | Apex o subdomain a attachar |

Tambien define `COMMON_ENV_VARS` (NODE_VERSION, PNPM_VERSION,
BASE_DOMAIN, BASE_SCHEME) y `GITHUB_OWNER`/`GITHUB_REPO`/`PRODUCTION_BRANCH`.

### `payloads.py`

Centraliza las JSON shapes:
- `build_create_project_payload(app)` — body del POST de creacion
- `build_patch_project_payload(app)` — body del PATCH (update sin recrear)

Helper `_env_vars()` convierte `{k: v}` plano a la shape correcta
`{k: {"type": "plain_text", "value": v}}`.

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

### `main.py`

Orquestador. Cada fase es idempotente — chequea state antes de mutar:

```python
def phase_projects(client):
    for app in APPS:
        existing = client.get_project(app.project_name)
        if existing is None:
            client.create_project(build_create_project_payload(app))
        else:
            client.patch_project(app.project_name, build_patch_project_payload(app))
```

## Fases disponibles

```bash
devtools/.venv/bin/python -m devtools.cloudflare_setup.main <phase>
```

| Phase | Que hace | Idempotente? |
|-------|----------|--------------|
| `projects` | Crea o patchea los 6 proyectos | si (create si no existe, patch si existe) |
| `domains` | Attacha custom domains a sus proyectos | si (skip si ya attached) |
| `dns` | Crea/actualiza CNAMEs en la zona | si (PUT replaces si target cambio) |
| `status` | Imprime ultimo deployment por proyecto | si (read-only) |
| `trigger` | Trigger deploy manual de cada proyecto | si (devuelve 304 si commit ya deployado) |
| `all` | Corre projects → domains → dns → status | si |

## Credenciales

```bash
# Cargar desde tmp/cloudflare-creds.env (gitignored)
set -a; . tmp/cloudflare-creds.env; set +a
```

Contenido del file:
```
CLOUDFLARE_API_TOKEN=v1.0_xxx...
ACCOUNT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Template (commiteado): `tmp/cloudflare-creds.env.template`.

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
           custom_domain='nueva.the-full-stack.com',
       ),
   )
   ```
3. Cargar credenciales y correr:
   ```bash
   set -a; . tmp/cloudflare-creds.env; set +a
   devtools/.venv/bin/python -m devtools.cloudflare_setup.main all
   ```

El script:
- Crea el proyecto (skip los 6 existentes)
- Attacha el domain (skip los 6 existentes)
- Crea el CNAME apuntando al subdomain real del proyecto nuevo
- Imprime status

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

## Lint check

```bash
cd devtools
uv run --frozen ruff check cloudflare_setup/
```

El modulo respeta el ruff config de `devtools/ruff.toml` (Python 3.14,
line-length 80, single quotes para tecnicos).
