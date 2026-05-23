# Fase F — Workflow deploy-apps.yml (multi-env)

> Reemplaza el `deploy.yml` actual (solo main) por `deploy-apps.yml`
> que dispara en push a `dev`/`stage`/`main`. Mapeo:
> dev -> `portfolio-{niche}-dev` (subdominios `*.portfolio.dev.the-full-stack.com`),
> stage -> `portfolio-{niche}-stage`,
> main -> `portfolio-{niche}` (canonical).

## Contexto / Problema

Hoy `deploy.yml`:

```yaml
on:
  push:
    branches: [main]
```

Solo despliega prod. Los proyectos Pages para dev/stage existen (18
proyectos en total) pero no tienen automatizacion.

Cada app Astro (`apps/{generic,hub,fintech,architect,leader,vibe}`)
buildea a `dist/` con `pnpm --filter @portfolio/{niche} run build`.

## Solucion

### F.1 — Estructura del workflow

```yaml
name: Deploy Apps

on:
  push:
    branches: [dev, stage, main]
  workflow_dispatch:
    inputs:
      env:
        description: "Environment to deploy to"
        required: true
        type: choice
        options: [dev, stage, main]

# Queue por env para alinearse con deploy-backend.yml.
concurrency:
  group: deploy-apps-${{ github.ref_name }}
  cancel-in-progress: false

env:
  NODE_VERSION: "24"
  PNPM_VERSION: "11.0.9"

jobs:
  # ---------------------------------------------------------------------------
  # Resolve env -> cloudflare project suffix
  # ---------------------------------------------------------------------------
  resolve-env:
    name: Resolve env (${{ github.ref_name }})
    runs-on: ubuntu-24.04
    outputs:
      stage: ${{ steps.resolve.outputs.stage }}
      project-suffix: ${{ steps.resolve.outputs.project-suffix }}
    steps:
      - id: resolve
        run: |
          case "${{ github.ref_name }}" in
            dev)
              echo "stage=dev"               >> "$GITHUB_OUTPUT"
              echo "project-suffix=-dev"     >> "$GITHUB_OUTPUT"
              ;;
            stage)
              echo "stage=stage"             >> "$GITHUB_OUTPUT"
              echo "project-suffix=-stage"   >> "$GITHUB_OUTPUT"
              ;;
            main)
              echo "stage=prod"              >> "$GITHUB_OUTPUT"
              echo "project-suffix="         >> "$GITHUB_OUTPUT"
              ;;
          esac

  # ---------------------------------------------------------------------------
  # Build de todas las apps. Reutiliza el artifact dist-all-apps-<sha> que
  # ci.yml (Fase D) ya subio. Si por alguna razon no esta, builda aqui.
  # ---------------------------------------------------------------------------
  build-apps:
    name: Build apps
    needs: resolve-env
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4

      - name: Try to download CI artifact (dist)
        id: try-artifact
        uses: actions/download-artifact@v4
        with:
          name: dist-all-apps-${{ github.sha }}
          path: apps/
        continue-on-error: true

      - name: Setup pnpm (only if rebuild needed)
        if: steps.try-artifact.outcome == 'failure'
        uses: pnpm/action-setup@v4
        with:
          version: ${{ env.PNPM_VERSION }}

      - name: Setup Node (only if rebuild needed)
        if: steps.try-artifact.outcome == 'failure'
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: pnpm

      - name: Install deps (only if rebuild needed)
        if: steps.try-artifact.outcome == 'failure'
        run: pnpm install --frozen-lockfile

      - name: Build (only if rebuild needed)
        if: steps.try-artifact.outcome == 'failure'
        run: |
          pnpm --filter @portfolio/cv-filters run build
          pnpm -r --filter "./apps/*" --workspace-concurrency=6 run build

      # Re-upload el artifact con un nombre estable para los matrix jobs.
      - name: Re-upload artifact for matrix
        uses: actions/upload-artifact@v4
        with:
          name: deploy-dist-${{ github.run_id }}
          path: apps/*/dist
          retention-days: 1

  # ---------------------------------------------------------------------------
  # Deploy de las 6 apps en paralelo. Cada una a su proyecto Cloudflare
  # Pages segun el env.
  # ---------------------------------------------------------------------------
  deploy-pages:
    name: Deploy ${{ matrix.niche }}
    needs: [resolve-env, build-apps]
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    strategy:
      fail-fast: false
      matrix:
        niche: [generic, hub, fintech, architect, leader, vibe]
    steps:
      - uses: actions/checkout@v4

      - name: Download dist artifact
        uses: actions/download-artifact@v4
        with:
          name: deploy-dist-${{ github.run_id }}
          path: apps/

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: pages deploy apps/${{ matrix.niche }}/dist --project-name=portfolio-${{ matrix.niche }}${{ needs.resolve-env.outputs.project-suffix }} --branch=${{ github.ref_name }}
```

### F.2 — Mapeo env -> proyecto Cloudflare Pages

| Branch | Stage | Project Pages | URL canonical |
|--------|-------|---------------|----------------|
| dev | dev | `portfolio-{niche}-dev` | `{niche}.portfolio.dev.the-full-stack.com` |
| stage | stage | `portfolio-{niche}-stage` | `{niche}.portfolio.stage.the-full-stack.com` |
| main | prod | `portfolio-{niche}` (sin sufijo) | `{niche}.portfolio.the-full-stack.com` (apex para `generic`) |

Excepcion: `generic` en prod = apex `the-full-stack.com`. Esa URL ya
esta configurada en el proyecto `portfolio-generic`. El workflow no
distingue, solo deploya el dist al proyecto correspondiente. Las DNS
ya estan.

### F.3 — Reuso del artifact de ci.yml

`ci.yml` (Fase D) sube `dist-all-apps-<sha>`. `deploy-apps.yml`
intenta descargarlo primero:

- Si existe (CI corrio antes en el push): saltamos rebuild. Ahorra
  ~30s.
- Si no existe (ej. push directo a main, sin PR previo): rebuild.

Esto requiere que `ci.yml` corra ANTES que `deploy-apps.yml` en el
mismo push. GitHub Actions dispara ambos workflows en paralelo, asi
que el artifact puede no estar listo. Compensacion: el step de
download tiene `continue-on-error: true` + fallback a build local.

Alternativa simple si la sincronizacion da problemas: NO reusar el
artifact, siempre rebuild. Costo: +30s por workflow. Trade-off
documentado.

### F.4 — Migracion del workflow viejo

`deploy.yml` actual:
- `on: push: branches: [main]`
- `detect-changes` con `git diff HEAD^` (por app).
- 1 job por app cambiado.

Nuevo `deploy-apps.yml`:
- 3 branches en `on:`.
- NO detect-changes (apps siempre rebuild + deploy).
- Matrix paralelo de 6 apps.

El viejo se borra al mergear el plan. Se renombra a `deploy-apps.yml`
en este commit y se sobreescribe el contenido.

## Archivos afectados

### Renombrar + sobreescribir

- `.github/workflows/deploy.yml` -> `.github/workflows/deploy-apps.yml`
  con el contenido nuevo.

## Criterios de aceptacion

- **AC-F1**: Given un push a `dev`, When inspecciono el workflow,
  Then `resolve-env` resuelve `stage=dev` y
  `project-suffix=-dev`.
- **AC-F2**: Given un push a `main`, Then `project-suffix=""` (sin
  sufijo).
- **AC-F3**: Given el workflow corre, When `build-apps` encuentra el
  artifact `dist-all-apps-<sha>` (CI corrio antes), Then NO rebuilda.
- **AC-F4**: Given el workflow corre y NO encuentra el artifact, Then
  rebuilda con `pnpm install + build`.
- **AC-F5**: Given el matrix de `deploy-pages`, When una app falla
  (ej. project name typo), Then los otros 5 deploys siguen
  (`fail-fast: false`).
- **AC-F6**: Given 2 pushes seguidos a `dev`, Then el segundo workflow
  se encola y espera al primero.

## Verificacion

```bash
# actionlint del workflow nuevo
actionlint .github/workflows/deploy-apps.yml

# Verificar que los 18 proyectos Cloudflare Pages existen:
for env in '' '-dev' '-stage'; do
  for niche in generic hub fintech architect leader vibe; do
    project="portfolio-${niche}${env}"
    curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
      "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/$project" \
      | jq -r '.result.name // "MISSING"'
  done
done
```

## Commit

```text
feat(ci): workflow deploy-apps.yml multi-env (dev/stage/main)

- Reemplaza .github/workflows/deploy.yml por deploy-apps.yml
- Dispara en push a dev/stage/main + workflow_dispatch manual
- Mapeo env -> proyecto Cloudflare Pages: dev -> portfolio-{niche}-dev,
  stage -> portfolio-{niche}-stage, main -> portfolio-{niche}
- 3 jobs: resolve-env -> build-apps -> deploy-pages (matrix 6 niches
  paralelo, fail-fast=false)
- build-apps intenta reusar el artifact dist-all-apps-<sha> que sube
  ci.yml (Fase D); si no esta, rebuild local
- concurrency.group=deploy-apps-${branch} + cancel-in-progress=false:
  alineado con deploy-backend.yml (queue por env)
- Conserva los 2 secretos existentes: CLOUDFLARE_API_TOKEN y
  CLOUDFLARE_ACCOUNT_ID"
```
