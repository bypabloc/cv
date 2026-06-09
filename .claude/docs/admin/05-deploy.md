# 05 — Deploy: Cloudflare Pages + devtools + GH Actions + env vars

[< 04-auth](04-auth.md) | [Siguiente: 06-testing >](06-testing.md)

## Setup global del deploy

| Item | Valor |
|------|-------|
| Provider | Cloudflare Pages (REST API) |
| Account | mismo que las 6 apps Astro |
| Projects | 2: `portfolio-admin-dev`, `portfolio-admin` (prod) |
| Branch mapping | `dev` → dev project, `main` → prod |
| Build command | `pnpm install --frozen-lockfile && pnpm --filter @portfolio/admin... build` |
| Output dir | `admin/out/` |
| Custom domains | `admin.portfolio.{dev|prod}.the-full-stack.com` |
| SSL | Cloudflare ACM (auto, per-hostname) |
| DNS records | CNAME `admin.portfolio.<env>` → `portfolio-admin-<env>.pages.dev` |

## Subdominios cumplen subdomain-standard

```
[{component}.]{product}.{env}.{domain}

admin.portfolio.dev.the-full-stack.com    (dev)
admin.portfolio.the-full-stack.com        (prod, env omitido)
```

Compliance ✅. `admin` es un component nuevo bajo el product `portfolio`.
Agregar a la lista de reservados de `subdomain-standard`:

```yaml
reserved:
  - generic, hub, fintech, architect, leader, vibe   # niches
  - admin   # panel admin (NEW)
```

## Extension de `devtools/cloudflare_setup/config.py`

El script `devtools/cloudflare_setup/` actualmente maneja las 6 apps
Astro. Hay que extenderlo para incluir el admin Next.js.

```python
"""devtools/cloudflare_setup/config.py — extension parcial."""

from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    """Una app del monorepo."""
    project_name: str        # 'admin'
    package_name: str         # '@portfolio/admin'
    root_dir: str             # 'admin'
    app_type: str = 'astro'   # 'astro' | 'nextjs'
    build_output_dir: str = 'dist'  # 'dist' para Astro, 'out' para Next

# 6 apps Astro existentes
APPS_ASTRO: tuple[AppConfig, ...] = (
    AppConfig(project_name='generic',   package_name='@portfolio/generic',   root_dir='apps/generic',   build_output_dir='dist'),
    AppConfig(project_name='hub',       package_name='@portfolio/hub',       root_dir='apps/hub',       build_output_dir='dist'),
    AppConfig(project_name='fintech',   package_name='@portfolio/fintech',   root_dir='apps/fintech',   build_output_dir='dist'),
    AppConfig(project_name='architect', package_name='@portfolio/architect', root_dir='apps/architect', build_output_dir='dist'),
    AppConfig(project_name='leader',    package_name='@portfolio/leader',    root_dir='apps/leader',    build_output_dir='dist'),
    AppConfig(project_name='vibe',      package_name='@portfolio/vibe',      root_dir='apps/vibe',      build_output_dir='dist'),
)

# Nuevo: admin Next.js (NO en apps/, sino en root como admin/)
APP_ADMIN: AppConfig = AppConfig(
    project_name='admin',
    package_name='@portfolio/admin',
    root_dir='admin',               # carpeta nueva en root
    app_type='nextjs',
    build_output_dir='out',          # Next.js export default
)

APPS: tuple[AppConfig, ...] = APPS_ASTRO + (APP_ADMIN,)

# Helpers de path
def output_dir_for(app: AppConfig) -> str:
    """Path al output dir para Cloudflare Pages destination."""
    return f'{app.root_dir}/{app.build_output_dir}'

def build_command_for(app: AppConfig) -> str:
    """Build command (idem para Astro y Next con pnpm)."""
    return f'pnpm install --frozen-lockfile && pnpm --filter {app.package_name}... build'
```

> El cambio clave es `build_output_dir`: Astro = `dist`, Next.js = `out`.
> El `project_name` del admin es `admin` (sufijo `-dev`
> o sin sufijo en prod via la logica existente del script).

## Custom domain wiring

```python
# devtools/cloudflare_setup/config.py — custom domain mapping

def custom_domain_for(app: AppConfig, env: str) -> str:
    """Resuelve el custom domain de cada app x env."""
    if app.project_name == 'generic' and env == 'prod':
        return 'the-full-stack.com'   # apex
    if app.project_name == 'admin':
        # admin.portfolio.{env}.the-full-stack.com
        if env == 'prod':
            return 'admin.portfolio.the-full-stack.com'
        return f'admin.portfolio.{env}.the-full-stack.com'
    # niches: {niche}.portfolio.{env}.the-full-stack.com
    if env == 'prod':
        return f'{app.project_name}.portfolio.the-full-stack.com'
    return f'{app.project_name}.portfolio.{env}.the-full-stack.com'
```

## Env vars del project Cloudflare Pages

Cuando devtools provisiona el project (fase `projects`), setea env vars
en el project que Cloudflare expone al build:

```python
def env_vars_for(app: AppConfig, env: str) -> dict[str, str]:
    base = {
        'NODE_VERSION': '24',
        'PNPM_VERSION': '11.0.9',
        'BASE_SCHEME': 'https',
        'BASE_DOMAIN': f'portfolio.{env}.the-full-stack.com' if env != 'prod' else 'portfolio.the-full-stack.com',
    }
    if env == 'prod':
        base['APEX_DOMAIN'] = 'the-full-stack.com'

    # Vars del API endpoint (compartido entre Astro y Next)
    base['PUBLIC_API_ENDPOINT'] = f'https://api.portfolio.{env}.the-full-stack.com' if env != 'prod' else 'https://api.portfolio.the-full-stack.com'
    base['PUBLIC_TURNSTILE_SITEKEY'] = '0x4AAAAAADPSoiQA_-LcRafo'

    # Vars exclusivas del admin (Next.js prefix NEXT_PUBLIC_)
    if app.project_name == 'admin':
        base['NEXT_PUBLIC_API_ENDPOINT'] = base['PUBLIC_API_ENDPOINT']
        base['NEXT_PUBLIC_TURNSTILE_SITEKEY'] = base['PUBLIC_TURNSTILE_SITEKEY']
        base['NEXT_PUBLIC_DASHBOARD_URL'] = f'https://{custom_domain_for(app, env)}'
        base['NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS'] = '30000'

    return base
```

## Extension de `docker/env/client/.example`

Agregar al template las nuevas vars del admin:

```bash
# Existente (apps Astro)
BASE_DOMAIN=
BASE_SCHEME=
APEX_DOMAIN=
PUBLIC_API_ENDPOINT=
PUBLIC_TURNSTILE_SITEKEY=
TURNSTILE_SITE_KEY=
TURNSTILE_ENABLED=

# Nuevo: admin (Next.js requiere prefix NEXT_PUBLIC_)
NEXT_PUBLIC_API_ENDPOINT=
NEXT_PUBLIC_TURNSTILE_SITEKEY=
NEXT_PUBLIC_DASHBOARD_URL=
NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS=30000
```

## Extension de `devtools/sync_secrets/catalog.py`

```python
CATALOG['NEXT_PUBLIC_API_ENDPOINT'] = SecretDefinition(
    name='NEXT_PUBLIC_API_ENDPOINT',
    type='client',
    description='API endpoint del Lambda backend (Next.js prefix)',
)
CATALOG['NEXT_PUBLIC_TURNSTILE_SITEKEY'] = SecretDefinition(
    name='NEXT_PUBLIC_TURNSTILE_SITEKEY',
    type='client',
    description='Turnstile sitekey publico (Next.js prefix)',
)
CATALOG['NEXT_PUBLIC_DASHBOARD_URL'] = SecretDefinition(
    name='NEXT_PUBLIC_DASHBOARD_URL',
    type='client',
    description='Self URL del admin (callbacks)',
)
CATALOG['NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS'] = SecretDefinition(
    name='NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS',
    type='client',
    description='ms antes del exp del JWT para refresh proactivo',
)
```

Sincronizar:

```bash
python devtools/run.py sync_secrets --env=dev --category=client --dry-run
python devtools/run.py sync_secrets --env=dev --category=client
```

## `.github/workflows/deploy-apps.yml` extension

El matrix actual tiene 6 niches Astro. Para incluir el admin,
agregar entradas explicitas con `include` (mejor que extender `matrix:
niche`).

Snippets relevantes:

```yaml
jobs:
  build-apps:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    environment: ${{ needs.resolve-env.outputs.stage }}
    env:
      BASE_DOMAIN: ${{ vars.BASE_DOMAIN }}
      BASE_SCHEME: ${{ vars.BASE_SCHEME }}
      APEX_DOMAIN: ${{ vars.APEX_DOMAIN }}
      PUBLIC_API_ENDPOINT: ${{ vars.PUBLIC_API_ENDPOINT }}
      PUBLIC_TURNSTILE_SITEKEY: ${{ vars.PUBLIC_TURNSTILE_SITEKEY }}
      # Vars exclusivas del admin
      NEXT_PUBLIC_API_ENDPOINT: ${{ vars.NEXT_PUBLIC_API_ENDPOINT }}
      NEXT_PUBLIC_TURNSTILE_SITEKEY: ${{ vars.NEXT_PUBLIC_TURNSTILE_SITEKEY }}
      NEXT_PUBLIC_DASHBOARD_URL: ${{ vars.NEXT_PUBLIC_DASHBOARD_URL }}
      NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS: ${{ vars.NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS }}
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: {version: 11.0.9}
      - uses: actions/setup-node@v4
        with: {node-version: 24, cache: pnpm}
      - run: pnpm install --frozen-lockfile
      - name: Build all apps (Astro + admin Next)
        run: |
          # Builds en paralelo: 6 Astro + 1 Next = 7 packages
          pnpm -r --filter "./apps/*" --filter "@portfolio/admin" \
            --workspace-concurrency=7 run build
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: deploy-dist-${{ github.run_id }}
          path: |
            apps/*/dist
            admin/out
          retention-days: 1

  deploy-pages:
    needs: [resolve-env, build-apps]
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    strategy:
      fail-fast: false
      matrix:
        include:
          - name: generic
            dist-dir: apps/generic/dist
            project: generic
          - name: hub
            dist-dir: apps/hub/dist
            project: hub
          - name: fintech
            dist-dir: apps/fintech/dist
            project: fintech
          - name: architect
            dist-dir: apps/architect/dist
            project: architect
          - name: leader
            dist-dir: apps/leader/dist
            project: leader
          - name: vibe
            dist-dir: apps/vibe/dist
            project: vibe
          - name: admin
            dist-dir: admin/out
            project: admin
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: deploy-dist-${{ github.run_id }}
          path: .
      - name: Deploy ${{ matrix.name }}
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: >
            pages deploy ${{ matrix.dist-dir }}
            --project-name=portfolio-${{ matrix.project }}${{ needs.resolve-env.outputs.project-suffix }}
            --branch=${{ github.ref_name }}

  verify-deploy:
    needs: [resolve-env, deploy-pages]
    runs-on: ubuntu-24.04
    strategy:
      fail-fast: false
      matrix:
        name: [generic, hub, fintech, architect, leader, vibe, admin]
    steps:
      - name: Resolve expected URL
        id: url
        run: |
          stage="${{ needs.resolve-env.outputs.stage }}"
          name="${{ matrix.name }}"
          if [[ "$name" == "admin" ]]; then
            [[ "$stage" == "prod" ]] && url="https://admin.portfolio.the-full-stack.com" || url="https://admin.portfolio.${stage}.the-full-stack.com"
          elif [[ "$name" == "generic" && "$stage" == "prod" ]]; then
            url="https://the-full-stack.com"
          else
            [[ "$stage" == "prod" ]] && url="https://${name}.portfolio.the-full-stack.com" || url="https://${name}.portfolio.${stage}.the-full-stack.com"
          fi
          echo "url=$url" >> "$GITHUB_OUTPUT"
      - name: Verify HTTP 200
        run: |
          set -e
          curl -sI "${{ steps.url.outputs.url }}" | head -1 | grep -q "200"
```

## CI: `ci.yml` extension

El `ci.yml` actual hace lint + build de las apps. Extender para incluir
el admin:

```yaml
- name: Lint & build all apps
  run: |
    pnpm run lint
    pnpm -r --filter "./apps/*" --filter "@portfolio/admin" \
      --workspace-concurrency=7 run build
```

## `pnpm-workspace.yaml`

```yaml
packages:
  - 'apps/*'
  - 'admin'          # NUEVO
  - 'packages/*'

allowBuilds:
  esbuild: true
  sharp: true
  # Next.js puede traer postinstall extra: monitor con verbose install
```

## Local dev: 2 opciones

### Opcion A — Next dev directo (recomendado para snappy HMR)

```bash
pnpm install                                       # workspace install
pnpm --filter @portfolio/admin dev                 # http://localhost:3000
```

Pro: Turbopack HMR rapido. Contra: no entra al nginx local (mappear via
`/etc/hosts` o `admin.localhost`).

### Opcion B — Docker compose con nginx

Si necesitas testear `admin.localhost:9970`:

```yaml
# docker/docker-compose/local.yml (extension)
services:
  admin:
    build:
      context: ../..
      dockerfile: docker/dockerfiles/admin.local.Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - ../../admin:/app/admin:cached
    network_mode: host
    command: pnpm --filter @portfolio/admin dev
    environment:
      NEXT_PUBLIC_API_ENDPOINT: http://api.localhost:9970
      NEXT_PUBLIC_TURNSTILE_SITEKEY: 0x4AAAAAADPSoiQA_-LcRafo
      NEXT_PUBLIC_DASHBOARD_URL: http://admin.localhost:9970
```

nginx ruteo `admin.localhost:9970 → admin:3000`. Mas pesado, mejor
parity con prod.

Decision: arrancar con Opcion A (mas rapido), agregar Opcion B solo si
necesario.

## Verificacion del deploy

```bash
# 1. Provisionar projects (primera vez por env)
export CLOUDFLARE_API_TOKEN="$(grep -m1 '^CLOUDFLARE_API_TOKEN=' docker/env/dev-cli/.prod | cut -d= -f2-)"
export ACCOUNT_ID="$(grep -m1 '^CLOUDFLARE_ACCOUNT_ID=' docker/env/dev-cli/.prod | cut -d= -f2-)"
python devtools/run.py cloudflare_setup all --env=dev

# 2. Verificar status
python devtools/run.py cloudflare_setup status --env=dev

# 3. Trigger primera build manual
python devtools/run.py cloudflare_setup trigger --env=dev

# 4. Esperar 2-3 min y verificar URL responde
curl -sI https://admin.portfolio.dev.the-full-stack.com/ | head -3

# 5. Verificar SSL cert OK
openssl s_client -connect admin.portfolio.dev.the-full-stack.com:443 -showcerts < /dev/null 2>&1 | grep -E '(subject|issuer)'

# 6. Verificar CSP en respuesta
curl -sI https://admin.portfolio.dev.the-full-stack.com/ | grep -i 'content-security-policy'
```

## Branch flow del deploy

Sigue el patron del repo (rule `git-workflow.md`):

```text
feature/admin-X → PR → dev  → auto-deploy dev (admin.portfolio.dev.the-full-stack.com)
                              ↓
                       PR → main → auto-deploy prod
```

Merge commit en todos los PRs (rebase forbidden — ver memory
`release-flow-rebase-divergence`).

## Cloudflare Pages caveats

| Caveat | Workaround |
|--------|-----------|
| Custom domain con random suffix → 403 | Esperar 2-3 min post-attach; ACM emite cert async |
| `preview_branch_includes` ausente → builds en todas las branches | Setear `preview_branch_includes: [<branch>]` per env (ver memory `cloudflare-pages-preview-branch-fix`) |
| `_headers` para `/` no aplica si Next genera `/index.html` | El `/*` cubre ambos. Si necesitas algo especial para `/`, agregar `/` explicitamente arriba de `/*` |
| CSP que rompe shadcn dialog portal | `style-src 'unsafe-inline'` necesario (Radix portales inyectan styles inline) |
| `node_modules` cache stale en Pages | Pages no cachea — siempre `pnpm install --frozen-lockfile` |
| Build > 25min | Optimizar: workspace-concurrency, lazy load deps |
| Bundle > 25 MB | code splitting agresivo, dynamic imports |

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Usar `wrangler` para crear el project | No soporta git-connected con env vars correctos | REST API via `cloudflare_setup` |
| Editar config del project en Cloudflare UI | El siguiente `cloudflare_setup projects` lo revierte | Editar `config.py` y re-run |
| Olvidar `environment: <stage>` en `deploy-apps.yml` | GH vars caen al default (prod), build sale roto en dev | Setear `environment` explicito por job |
| Hardcodear el sitekey Turnstile en `next.config.ts` | Acopla con rotacion | `NEXT_PUBLIC_TURNSTILE_SITEKEY` env var |
| Olvidar `admin/out` en upload-artifact | Deploy descarga vacio | Path explicito con `|` multi-line |
| `cancel-in-progress: true` en deploy | Cancela mid-deploy = AWS state parcial | `cancel-in-progress: false` |
| Push directo a `dev`/`main` | Branches protegidas (rulesets) | PR con merge commit |
| `wrangler.toml` con `name` distinto al project Cloudflare | wrangler crea uno nuevo | NO usar wrangler.toml — todo via devtools |
| Setear `NEXT_PUBLIC_*` como GH Secret | Mascarea en logs, dificulta debug | Como GH Variable (publico por contrato) |

[< 04-auth](04-auth.md) | [Siguiente: 06-testing >](06-testing.md)
