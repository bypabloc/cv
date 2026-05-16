# CI Workflow del Proyecto

> Estructura, flujo y como probar el workflow de GitHub Actions con act.

## Workflow actual

Archivo: `.github/workflows/ci.yml`

```yaml
name: Portfolio CI

on:
  pull_request:
    branches: ["main", "master", "dev"]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - Checkout (fetch-depth: 0)
      - Setup uv 0.9.30 (astral-sh/setup-uv@v3, cachea wheels via devtools/uv.lock)
      - Install devtools dependencies (uv sync --frozen --project devtools)
      - Detect changed areas (uv run --project devtools python .git-hooks/_ci_detect.py)
      - Create Docker env file (docker/env/.test)
      - Build and start Docker services (test env)
      - Run quality gates (uv run --project devtools python .git-hooks/pre-push)
      - Stop Docker services (always)
```

### Flujo de ejecucion

```
PR creado/actualizado
    |
    v
GitHub Actions trigger (pull_request)
    |
    v
Job: quality-gates (ubuntu-latest, 30min timeout)
    |
    +-- 1. Checkout repo completo (fetch-depth: 0 para diff)
    +-- 2. uv 0.9.30 + uv sync --frozen --project devtools (Python 3.14 nativo)
    +-- 3. Crear docker/env/.test con credenciales CI
    +-- 4. docker compose up (test env, puerto 9977)
    +-- 5. python3 .git-hooks/pre-push
    |       +-- Conformance (Ruff lint)
    |       +-- Coverage (unit tests >= 80%)
    |       +-- Integration tests
    +-- 6. docker compose down (always, incluso si falla)
```

### Zero duplicacion

El CI ejecuta el mismo script que el hook local: `.git-hooks/pre-push`. Cambios en el hook se reflejan automaticamente en CI.

## Variables de entorno del CI

El portfolio es un monorepo Astro estatico sin backend ni DB. El workflow
solo pinea las versiones del toolchain en el bloque `env` global:

```yaml
env:
  NODE_VERSION: "24"
  PNPM_VERSION: "11.0.9"
```

No hay credenciales de DB ni secrets de runtime: el CI compila sitios
estaticos. El job `e2e-tests` que levanta Docker usa los `docker/env/.test`
versionados, sin secretos sensibles.

## Probar CI localmente con act

### Setup inicial (una vez)

```bash
# 1. Instalar act
brew install act

# 2. El proyecto ya incluye .actrc con configuracion optima
#    Si no existe, crear con:
cat > .actrc << 'EOF'
-P ubuntu-latest=-self-hosted
--env CI=true
--env DOCKER_ENV=test
EOF

# 3. Crear .secrets (no se committea)
cat > .secrets << 'EOF'
GITHUB_TOKEN=ghp_tu_token_aqui
EOF
```

### Comandos para probar

```bash
# === Validacion rapida (sin ejecutar) ===
act -n                          # Dry run: valida YAML y resuelve dependencias
act --validate                  # Solo validar sintaxis del workflow
act -l                          # Listar jobs disponibles
act -g                          # Grafo de dependencias

# === Ejecutar CI completo ===
act pull_request                # Simula PR event (trigger del workflow)

# === Ejecutar job especifico ===
act -j quality-gates            # Solo el job quality-gates

# === Debug ===
act pull_request --verbose      # Logs detallados
act pull_request --reuse        # Reusar contenedores (mas rapido en iteraciones)

# === Watch mode (re-ejecuta al cambiar archivos) ===
act pull_request -w
```

### Flujo recomendado para cambios en CI

```bash
# 1. Validar sintaxis del workflow
act --validate

# 2. Dry run para verificar resolucion de steps
act -n

# 3. Ejecutar completo con verbose
act pull_request --verbose

# 4. Si falla, iterar con --reuse para velocidad
act pull_request --reuse --verbose

# 5. Si pasa localmente, push con confianza
git push
```

## Modificar el workflow

### Agregar un step nuevo

```yaml
# En .github/workflows/ci.yml, agregar dentro de steps:
    - name: Mi nuevo step
      run: |
        echo "Ejecutando nuevo step"
        python devtools/run.py docker lint
```

### Agregar un step que no corra en act

```yaml
    - name: Notificar Slack
      if: ${{ !env.ACT }}
      run: |
        curl -X POST $SLACK_WEBHOOK_URL ...
```

### Agregar secretos al workflow

```yaml
    - name: Step con secreto
      env:
        API_KEY: ${{ secrets.API_KEY }}
      run: echo "Usando secreto"
```

Para act, agregar en `.secrets`:
```
API_KEY=mi_secreto_local
```

### Agregar matrix strategy

```yaml
jobs:
  quality-gates:
    strategy:
      matrix:
        python-version: ["3.13", "3.14"]
    steps:
    - uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
```

Para act: `act pull_request --matrix python-version:3.14`

## Troubleshooting

### act falla con Docker-in-Docker

El workflow ejecuta `docker compose` internamente. Solucion:

```bash
# Usar self-hosted (ejecuta en host, no en contenedor)
act -P ubuntu-latest=-self-hosted

# O montar socket Docker
act --container-options "-v /var/run/docker.sock:/var/run/docker.sock"
```

El `.actrc` del proyecto ya incluye `-P ubuntu-latest=-self-hosted`.

### Python 3.14 no disponible en imagen act

En modo self-hosted, act usa el Python del host. Verificar:
```bash
python3 --version  # Debe ser 3.14 o usar pyenv/uv
```

En modo contenedor, `actions/setup-python@v5` intenta instalar Python pero puede fallar en imagenes micro/medium. Usar imagen large o self-hosted.

### Step falla solo en act pero no en GitHub

1. Verificar variables de entorno: `act` no inyecta todas las `GITHUB_*` vars
2. Verificar secretos: `act` no tiene acceso a secretos de GitHub
3. Verificar networking: `act` usa `host` network, GitHub usa aisladas
4. Verificar checkout: `act` copia directorio local vs GitHub hace `git clone`

### act cuelga o tarda mucho

```bash
# Usar bind mount (evita copiar todo el repo)
act pull_request --bind

# Reusar contenedores entre ejecuciones
act pull_request --reuse

# Modo offline (no descarga actions)
act pull_request --action-offline-mode
```

## Relacion con git hooks

| Mecanismo | Que valida | Cuando | Entorno |
|-----------|-----------|--------|---------|
| `pre-commit` | Conformance + Coverage (staged) | `git commit` | Local (Docker para tests) |
| `pre-push` | Conformance + Coverage + Integration (unmerged) | `git push` | Local (Docker) |
| CI (`ci.yml`) | Lo mismo que pre-push | PR a main/master/dev | GitHub runner (Docker) |
| `act` | Lo mismo que CI | Manual, bajo demanda | Local (self-hosted) |

El valor de act es **validar cambios al workflow YAML** antes de hacer push. Para quality gates normales, los hooks locales son suficientes.
