# Fase E — Workflow deploy-backend.yml

> Workflow nuevo: en cada push a `dev`/`stage`/`main`, aplica
> migraciones de DB y redeploya los lambdas afectados. AWS via OIDC,
> state en S3, matrix paralelo por lambda.

## Contexto / Problema

Hoy: deploy de Lambdas = 100% manual. El usuario quiere que al
mergear a una rama de entorno, el CI lo haga.

Orden obligatorio: `migrate-db` -> `detect-changes` ->
`deploy-lambdas` (matrix paralelo). Si migrate-db falla, los otros
jobs NO se ejecutan.

## Solucion

### E.1 — Estructura del workflow

```yaml
name: Deploy Backend

on:
  push:
    branches: [dev, stage, main]

# Queue por env para evitar race conditions con S3 state.
concurrency:
  group: deploy-backend-${{ github.ref_name }}
  cancel-in-progress: false

permissions:
  id-token: write  # requerido para OIDC
  contents: read

env:
  AWS_REGION: us-east-1
  DEVTOOLS_STATE_BACKEND: s3
  DEVTOOLS_STATE_BUCKET: portfolio-devtools-state
  PYTHON_VERSION: "3.14"

jobs:
  # ---------------------------------------------------------------------------
  # Resolve env -> stage + IAM role ARN
  # ---------------------------------------------------------------------------
  resolve-env:
    name: Resolve env (${{ github.ref_name }})
    runs-on: ubuntu-24.04
    outputs:
      stage: ${{ steps.resolve.outputs.stage }}
      role-arn: ${{ steps.resolve.outputs.role-arn }}
    steps:
      - id: resolve
        run: |
          case "${{ github.ref_name }}" in
            dev)
              echo "stage=dev"     >> "$GITHUB_OUTPUT"
              echo "role-arn=arn:aws:iam::637423614564:role/portfolio-deploy-dev" >> "$GITHUB_OUTPUT"
              ;;
            stage)
              echo "stage=stage"   >> "$GITHUB_OUTPUT"
              echo "role-arn=arn:aws:iam::637423614564:role/portfolio-deploy-stage" >> "$GITHUB_OUTPUT"
              ;;
            main)
              echo "stage=prod"    >> "$GITHUB_OUTPUT"
              echo "role-arn=arn:aws:iam::637423614564:role/portfolio-deploy-prod" >> "$GITHUB_OUTPUT"
              ;;
          esac

  # ---------------------------------------------------------------------------
  # Apply DB migrations (Lambda `db` con event=migrate.json)
  # Si falla, el resto NO corre.
  # ---------------------------------------------------------------------------
  migrate-db:
    name: Apply DB migrations (${{ needs.resolve-env.outputs.stage }})
    needs: resolve-env
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ needs.resolve-env.outputs.role-arn }}
          aws-region: ${{ env.AWS_REGION }}

      # devtools bootstraps su .venv automaticamente con uv sync.
      - name: Setup devtools
        run: pip install uv

      # 1. Re-deploy del Lambda `db` (puede haber cambios en migrations,
      #    seeds excluidos por change_detector).
      - name: Re-deploy Lambda db
        run: |
          python devtools/run.py serverless deploy \
            --lambda=db --stage=${{ needs.resolve-env.outputs.stage }}

      # 2. Aplicar migrations: serverless run --lambda=db --event=events/migrate.json
      - name: Apply migrations
        run: |
          python devtools/run.py serverless run \
            --lambda=db \
            --stage=${{ needs.resolve-env.outputs.stage }} \
            --event=serverless/lambda/services/db/events/migrate.json

      - name: Show current revision
        run: |
          python devtools/run.py serverless run \
            --lambda=db \
            --stage=${{ needs.resolve-env.outputs.stage }} \
            --event=serverless/lambda/services/db/events/current.json

  # ---------------------------------------------------------------------------
  # Detect lambdas afectados (path-based + cierre transitivo de shared)
  # ---------------------------------------------------------------------------
  detect-changes:
    name: Detect affected lambdas
    needs: [resolve-env, migrate-db]
    runs-on: ubuntu-24.04
    outputs:
      affected: ${{ steps.detect.outputs.affected }}
      has-affected: ${{ steps.detect.outputs.has-affected }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # necesitamos historia para git diff

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Setup devtools
        run: pip install uv

      - id: detect
        name: Run change detector
        run: |
          # base: el sha previo al push (github.event.before). Si es 'zeros'
          # (primer push a la rama), usamos un fallback de 10 commits atras.
          base="${{ github.event.before }}"
          if [[ "$base" == "0000000000000000000000000000000000000000" ]]; then
            base=$(git rev-parse HEAD~10)
          fi
          head="${{ github.sha }}"

          # `db` ya fue redeployado en migrate-db; lo excluimos del matrix.
          output=$(python devtools/run.py serverless detect-changes \
            --base="$base" --head="$head" | jq -c '.affected | map(select(. != "db"))')

          echo "affected=$output" >> "$GITHUB_OUTPUT"
          echo "has-affected=$(jq 'length > 0' <<< "$output")" >> "$GITHUB_OUTPUT"

          echo "Affected lambdas: $output"

  # ---------------------------------------------------------------------------
  # Deploy de cada lambda afectado en paralelo.
  # ---------------------------------------------------------------------------
  deploy-lambdas:
    name: Deploy ${{ matrix.lambda }}
    needs: [resolve-env, detect-changes]
    if: needs.detect-changes.outputs.has-affected == 'true'
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    strategy:
      fail-fast: false  # si cv falla, queremos saber si los otros funcionaron
      matrix:
        lambda: ${{ fromJSON(needs.detect-changes.outputs.affected) }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ needs.resolve-env.outputs.role-arn }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Setup devtools
        run: pip install uv

      - name: Deploy ${{ matrix.lambda }}
        run: |
          python devtools/run.py serverless deploy \
            --lambda=${{ matrix.lambda }} \
            --stage=${{ needs.resolve-env.outputs.stage }}

      - name: Verify status
        run: |
          python devtools/run.py serverless status \
            --lambda=${{ matrix.lambda }} \
            --stage=${{ needs.resolve-env.outputs.stage }}
```

### E.2 — Decisiones de implementacion

| Decision | Razon |
|----------|-------|
| `migrate-db` SIEMPRE corre (no detect) | Las migrations son idempotentes (Alembic detecta y aplica solo lo nuevo). Es barato (~30s). Si no hay nada que aplicar, exit 0 |
| `db` se redeploya tambien en migrate-db (no en deploy-lambdas) | Necesitamos el Lambda actualizado ANTES de invocarlo para correr migrations. Por eso se excluye del matrix de detect-changes |
| `detect-changes` corre DESPUES de migrate-db | Mantiene el orden estricto. Si migrate falla, detect ni siquiera arranca |
| `strategy.fail-fast: false` | Si `cv` falla pero `contact_form` pasa, queremos saber. No abortar los otros |
| `concurrency.group=deploy-backend-${{ github.ref_name }}` | Queue por env. Dos pushes a dev seguidos: el segundo espera al primero |
| `cancel-in-progress: false` | No cancelar el primero — podria dejar AWS en estado parcial |

### E.3 — Que pasa si detect-changes no devuelve nada

`if: needs.detect-changes.outputs.has-affected == 'true'` — el job
`deploy-lambdas` simplemente no corre. Pero `migrate-db` SI corrio
(el redeploy del Lambda db + apply migrations). El workflow exit 0.

Casos donde detect-changes devuelve vacio:
- Cambio solo de docs (`docs/`, `*.md`).
- Cambio solo en `apps/` o `packages/` (eso lo maneja deploy-apps.yml).
- Cambio solo en tests/ o seeds/ del lambda db.

### E.4 — Outputs para deploy-apps.yml

El job `resolve-env` exporta el `stage` resuelto. `deploy-apps.yml`
(Fase F) lo replica con la misma logica. Si en el futuro se quiere
unificar, ambos workflows pueden referenciar un composite action.

## Archivos afectados

### Crear

- `.github/workflows/deploy-backend.yml` — workflow completo.
  - Verificar: smoke test desde la rama del plan (push a feature
    branch NO dispara; pero un PR mergeado a dev SI).

## Criterios de aceptacion

- **AC-E1**: Given un push a `dev`, When inspecciono el workflow,
  Then `resolve-env` resuelve `stage=dev` y `role-arn=...portfolio-deploy-dev`.
- **AC-E2**: Given el workflow corre, When `migrate-db` falla (ej.
  conexion Neon caida), Then `detect-changes` y `deploy-lambdas` NO
  corren.
- **AC-E3**: Given un push a dev que solo toco `serverless/lambda/services/cv/core/`,
  When `detect-changes` corre, Then `affected=["cv"]` (no `db`).
- **AC-E4**: Given un push a dev que toco solo `serverless/lambda/shared/core/`,
  When `detect-changes` corre, Then `affected` incluye todos los
  lambdas excepto `db` (que ya fue redeployado en migrate-db).
- **AC-E5**: Given 2 pushes seguidos a `dev` (con 5s de delta), Then
  el segundo workflow se encola y espera al primero (concurrency).

## Verificacion

```bash
# Pre-merge: validar la sintaxis del workflow con actionlint
actionlint .github/workflows/deploy-backend.yml

# Smoke: push a la branch del plan NO dispara (solo dev/stage/main).
# Despues de mergear: push directo a dev (NO recomendado en general, pero
# permitido para el smoke):
gh workflow run deploy-backend.yml --ref dev
gh run watch
```

## Commit

```text
feat(ci): workflow deploy-backend.yml (lambdas + migrations)

- Nuevo workflow .github/workflows/deploy-backend.yml dispara en push
  a dev/stage/main. Orden: resolve-env -> migrate-db -> detect-changes
  -> deploy-lambdas (matrix paralelo)
- resolve-env mapea branch -> stage + IAM role ARN OIDC
- migrate-db SIEMPRE corre: redeploya el Lambda db y aplica Alembic
  via serverless run --lambda=db --event=migrate.json. Si falla, el
  resto NO corre
- detect-changes invoca serverless detect-changes (Fase C) para listar
  los lambdas afectados; excluye db (ya redeployado)
- deploy-lambdas usa matrix.lambda con fail-fast=false: si cv falla,
  los otros lambdas siguen
- concurrency.group=deploy-backend-${branch} + cancel-in-progress=false:
  pushes seguidos al mismo env se encolan, no se cancelan
- Auth via aws-actions/configure-aws-credentials@v4 + OIDC. Cero
  secrets AWS de larga vida"
```
