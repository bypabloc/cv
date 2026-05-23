# Fase D — CI simplificado (PRs)

> Refactor `.github/workflows/ci.yml`: quita `typecheck`, `astro
> check`, `unit tests with coverage` y `Upload coverage`. Deja solo
> `biome check` + `build all apps`. Reduce duracion de ~80s a ~45s.

## Contexto / Problema

`ci.yml` hoy duplica lo que el pre-push hook local ya valida (lint +
typecheck + unit + coverage + build). El usuario SIEMPRE corre
pre-push antes de pushear. CI es la red de seguridad para casos
extremos (alguien hace `--no-verify` o un colaborador sin el hook
setup).

Anatomia de los ~80s actuales:

| Step | Duracion |
|------|----------|
| Provisioning runner + setup pnpm/node | ~10s |
| `pnpm install --frozen-lockfile` | ~2.5s |
| `biome check .` | ~1.5s |
| `tsc` typecheck (5 packages) | ~9.5s |
| `astro check` (6 apps) | ~20s |
| Vitest `--coverage` | ~10s |
| Upload coverage | ~0.7s |
| Build cv-filters | ~0.7s |
| Build 6 apps | ~20s |
| Upload dist | <1s |

Eliminando typecheck + astro check + unit + upload coverage: ~40s
ahorrados. Duracion proyectada: ~45s.

Trade-off aceptado:

- Si alguien hace `--no-verify` y mete un type error: el build del
  CI falla (Astro reporta los errores criticos en `astro build`,
  aunque sin todos los diagnostics de `astro check`).
- Si alguien mete un test roto via `--no-verify`: NO lo detecta CI.
  Lo detecta el reviewer del PR o el siguiente dev al pull. Riesgo
  aceptable porque el repo es 1 mantenedor.

## Solucion

### D.1 — Refactor `ci.yml`

```yaml
name: CI

on:
  pull_request:
    branches: [main, master, dev, stage]
  push:
    branches: [main, dev, stage]

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  NODE_VERSION: "24"
  PNPM_VERSION: "11.0.9"

jobs:
  # ---------------------------------------------------------------------------
  # Quality gates SIMPLIFICADO: solo conformance + build estatico.
  #
  # El pre-push hook local SIEMPRE corre la bateria completa (lint +
  # typecheck + unit + coverage + build + E2E). CI es la red de
  # seguridad para `--no-verify` y colaboradores sin el hook setup —
  # cubrir el subset que detecta deploys rotos basta.
  #
  # typecheck y unit tests viven en pre-push. astro check duplica el
  # parsing que ya hace astro build, asi que se elimina.
  # ---------------------------------------------------------------------------
  quality-gates:
    name: Lint + Build
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 1  # depth=1 alcanza (no necesitamos historia)

      - name: Setup pnpm ${{ env.PNPM_VERSION }}
        uses: pnpm/action-setup@v4
        with:
          version: ${{ env.PNPM_VERSION }}
          run_install: false

      - name: Setup Node ${{ env.NODE_VERSION }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: pnpm

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Biome check (lint + format)
        run: pnpm exec biome check .

      - name: Build cv-filters bundle (needed by apps prebuild)
        run: pnpm --filter @portfolio/cv-filters run build

      - name: Build all apps
        run: pnpm -r --filter "./apps/*" --workspace-concurrency=6 run build

      - name: Upload dist artifacts (deploy reusa)
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: dist-all-apps-${{ github.sha }}
          path: apps/*/dist
          retention-days: 7
          if-no-files-found: warn
```

### Cambios clave

| Cambio | Razon |
|--------|-------|
| Quito step `TypeScript check (packages)` | pre-push lo hace; el build falla si hay un import roto |
| Quito step `Astro check (apps)` | duplica parsing con build; el build reporta los errores criticos |
| Quito step `Unit tests with coverage` | pre-push lo hace; coverage no es required check |
| Quito step `Upload coverage artifacts` | Nadie los descarga hoy. Si se quiere visibilidad, Codecov en otro PR |
| Cambio `fetch-depth: 0` a `1` | No necesitamos historia para lint+build. Ahorra ~1s |
| Agrego `--workspace-concurrency=6` al build | pnpm paraleliza el build de las 6 apps. Ahorra ~10s |
| Mantengo `Upload dist artifacts` | El workflow `deploy-apps.yml` (Fase F) lo descarga para el deploy, evita rebuildear |
| Rename artifact key a `dist-all-apps-${{ github.sha }}` | Permite que deploy-apps.yml lo descargue por sha exacto |

### D.2 — Nota sobre el badge

El badge del PR cambia de `Lint + Typecheck + Unit + Build` a `Lint +
Build`. Cualquier rule de GitHub Branch Protection que requiera el
status check anterior se debe actualizar:

```bash
gh api repos/bypabloc/cv/branches/dev/protection/required_status_checks \
  -X PATCH -f contexts='["Lint + Build"]'
# idem para stage y main
```

(Documentado en el commit body para que el operador no se olvide.)

## Archivos afectados

### Modificar

- `.github/workflows/ci.yml` — refactor completo (ver arriba).
  - Verificar: el siguiente PR ejecuta el workflow nuevo en <60s.

## Criterios de aceptacion

- **AC-D1**: Given el ci.yml refactorizado, When abro un PR de prueba,
  Then aparece UN solo check `Lint + Build` (no 5 separados).
- **AC-D2**: Given el workflow corre en una PR vacia (cambio trivial),
  Then duracion total < 60s.
- **AC-D3**: Given un PR que rompe biome (faltó una coma final), Then
  el workflow falla en el step `Biome check` con exit 1.
- **AC-D4**: Given un PR que rompe el build de una app (import
  inexistente), Then el workflow falla en el step `Build all apps`.
- **AC-D5**: Given el workflow exitoso, When inspecciono los
  artifacts, Then existe `dist-all-apps-<sha>` con los `dist/` de las
  6 apps.

## Verificacion

```bash
# Despues del commit, abrir un PR de prueba:
git checkout -b test/ci-simplificado
echo "// trivial" >> apps/generic/src/pages/index.astro
git commit -am "test: trigger ci"
git push
gh pr create --base dev --title "test ci"

# Esperar a que CI corra. Inspeccionar duracion y steps:
gh run watch
gh run view --log
```

## Commit

```text
ci: simplifica ci.yml — solo lint + build, quita typecheck y unit

- Quita los steps TypeScript check, Astro check, Unit tests with
  coverage y Upload coverage artifacts del workflow CI
- pre-push hook local ya corre la bateria completa (lint + typecheck
  + unit + coverage + build + E2E). CI es la red de seguridad para
  --no-verify y colaboradores sin el hook
- astro check duplicaba el parsing con astro build; el build reporta
  los errores criticos (imports rotos, props mal tipadas que el
  bundler detecta)
- Agrega --workspace-concurrency=6 al build de las apps (ahorra ~10s
  paralelizando)
- Rename del artifact a dist-all-apps-<sha> para que deploy-apps.yml
  (Fase F) lo descargue sin rebuildear
- Duracion: ~80s -> ~45s
- IMPORTANTE: actualizar el required status check del branch
  protection rule (era 'Lint + Typecheck + Unit + Build', ahora
  'Lint + Build'). Ver commit body para el comando gh"
```
