# act - Referencia CLI

> Herramienta para ejecutar GitHub Actions localmente via Docker.

## Instalacion (WSL2/Linux)

```bash
# Recomendado (actualizaciones faciles)
brew install act

# Alternativa: script directo
curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Via GitHub CLI
gh extension install https://github.com/nektos/gh-act

# Via Go
go install github.com/nektos/act@latest
```

**Prerrequisito**: Docker Engine debe estar instalado y corriendo.

## Comandos core

```bash
# Ejecutar evento por defecto (push)
act

# Ejecutar evento especifico
act push
act pull_request
act workflow_dispatch

# Listar workflows (sin ejecutar)
act -l
act -l pull_request

# Dry run (valida sin crear contenedores)
act -n
act -n pull_request

# Ejecutar job especifico
act -j quality-gates

# Ejecutar workflow especifico
act -W '.github/workflows/ci.yml'

# Visualizar grafo de dependencias
act -g

# Validar sintaxis
act --validate

# Watch mode (re-ejecuta al detectar cambios)
act -w
```

## Flags de referencia

### Seleccion de workflow y jobs

| Flag | Short | Descripcion |
|------|-------|-------------|
| `--workflows` | `-W` | Path a workflows (default: `.github/workflows/`) |
| `--job` | `-j` | Ejecutar job especifico por ID |
| `--detect-event` | | Usar primer evento del workflow |
| `--directory` | `-C` | Directorio de trabajo |
| `--eventpath` | `-e` | Path a JSON de evento |
| `--matrix` | | Filtrar matrix (ej: `--matrix node:18`) |

### Control de ejecucion

| Flag | Short | Descripcion |
|------|-------|-------------|
| `--list` | `-l` | Listar workflows sin ejecutar |
| `--graph` | `-g` | Mostrar grafo de dependencias |
| `--dryrun` | `-n` | Validar sin crear contenedores |
| `--validate` | | Solo validar sintaxis YAML |
| `--watch` | `-w` | Re-ejecutar al detectar cambios |
| `--reuse` | `-r` | No eliminar contenedores tras exito |
| `--rm` | | Eliminar contenedores tras fallo |
| `--no-skip-checkout` | | Usar `actions/checkout` real |

### Contenedores y Docker

| Flag | Short | Descripcion |
|------|-------|-------------|
| `--platform` | `-P` | Imagen por plataforma (ej: `-P ubuntu-latest=img`) |
| `--pull` | `-p` | Forzar pull de imagenes (default: true) |
| `--bind` | `-b` | Bind mount en vez de copy (mas rapido) |
| `--container-architecture` | | Arquitectura (ej: `linux/amd64`) |
| `--container-daemon-socket` | | Socket Docker |
| `--container-options` | | Opciones Docker custom |
| `--network` | | Red Docker (default: `host`) |

### Secretos, variables y entorno

| Flag | Short | Descripcion |
|------|-------|-------------|
| `--secret` | `-s` | Secreto inline (ej: `-s KEY=val`) |
| `--secret-file` | | Archivo de secretos (default: `.secrets`) |
| `--var` | | Variable inline |
| `--var-file` | | Archivo de variables (default: `.vars`) |
| `--env` | | Variable de entorno inline |
| `--env-file` | | Archivo de env vars (default: `.env`) |
| `--input` | | Input inline (workflow_dispatch) |
| `--insecure-secrets` | | No enmascarar secretos en logs |

### Artefactos y cache

| Flag | Descripcion |
|------|-------------|
| `--artifact-server-path` | Directorio para artefactos |
| `--cache-server-path` | Directorio para cache (default: `~/.cache/actcache`) |
| `--action-cache-path` | Cache de actions (default: `~/.cache/act`) |
| `--action-offline-mode` | Modo offline (solo cache) |

### Output y debug

| Flag | Short | Descripcion |
|------|-------|-------------|
| `--verbose` | `-v` | Logs nivel debug |
| `--quiet` | `-q` | Suprimir output de steps |
| `--json` | | Logs en formato JSON |

## Configuracion

### `.actrc` — Flags por defecto

Archivo de configuracion con un argumento por linea. Prioridad de carga (ultimo gana):

1. `~/.config/act/actrc` (XDG)
2. `~/.actrc` (HOME)
3. `.actrc` (proyecto)
4. Argumentos CLI

```
-P ubuntu-latest=-self-hosted
--env CI=true
--env DOCKER_ENV=test
--secret-file .secrets
--artifact-server-path ./tmp/artifacts
```

### `.secrets` — Secretos (formato `.env`)

```
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
FERNET_KEY=dGVzdC1mZXJuZXQta2V5LWZvci1jaS1vbmx5LTEyMzQ=
```

Alternativas:
```bash
act -s MY_SECRET=somevalue              # Inline
act -s MY_SECRET                        # Lee de env var del host
act -s GITHUB_TOKEN="$(gh auth token)"  # Token via gh CLI
```

### `.vars` — Variables de repositorio

```
DEPLOY_ENV=staging
APP_VERSION=1.0.0
```

## Docker images (runners)

act ofrece 3 tamanos de imagen:

| Tamano | Imagen (`ubuntu-latest`) | Disco | Contenido |
|--------|--------------------------|-------|-----------|
| Micro | `node:16-buster-slim` | <200MB | Solo Node.js |
| Medium | `catthehacker/ubuntu:act-latest` | ~500MB | Herramientas esenciales |
| Large | `catthehacker/ubuntu:full-latest` | ~17GB | Replica del runner GitHub |

**Flag `-P` para imagenes custom**:
```bash
act -P ubuntu-latest=catthehacker/ubuntu:act-latest    # Medium
act -P ubuntu-latest=catthehacker/ubuntu:full-latest   # Large
act -P ubuntu-latest=-self-hosted                       # Ejecuta en host (sin contenedor)
```

## Self-hosted mode (RECOMENDADO para portfolio)

Cuando el workflow ejecuta Docker internamente (como portfolio con `docker compose`), usar `-self-hosted` evita Docker-in-Docker:

```bash
act -P ubuntu-latest=-self-hosted
```

Esto ejecuta los steps directamente en el host WSL2, donde Docker ya esta disponible.

**Alternativa (DinD)**:
```bash
act --container-options "-v /var/run/docker.sock:/var/run/docker.sock"
```

## Limitaciones

| Module | Limitacion | Impacto portfolio |
|------|-----------|-------------------|
| Docker-in-Docker | Workflow usa Docker Compose internamente | CRITICO: requiere `-self-hosted` o montar socket |
| Imagenes default | No contienen todas las herramientas | Medio: `actions/setup-python` con 3.14 puede fallar en micro/medium |
| Services | Soporte parcial de service containers | Ninguno: portfolio no usa `services:` |
| GITHUB_TOKEN | Debe proporcionarse manualmente | Bajo: portfolio no usa GITHUB_TOKEN para API calls |
| Cache action | Requiere `--cache-server-path` explicito | Ninguno: portfolio no usa `actions/cache` |
| Environment secrets | No soporta secretos por environment | Ninguno |
| Expression evaluator | Puede diferir en edge cases con `hashFiles()` | Bajo |

### Diferencias de comportamiento vs GitHub Actions

1. **Networking**: act usa `host` network; GitHub usa redes aisladas por job
2. **Filesystem**: act copia workspace al contenedor (o bind-mount con `--bind`); GitHub hace checkout fresco
3. **Default branch**: act no siempre detecta `github.event.repository.default_branch`
4. **Checkout**: act simula `actions/checkout` copiando el directorio actual (no hace git clone)

## Best practices

1. **Dry run primero**: `act -n` antes de ejecutar para validar
2. **`--reuse` para iteraciones rapidas**: Evita recrear contenedores
3. **`--bind` para workspace**: Mas rapido que copy en repos grandes
4. **`.actrc` en el proyecto**: Estandariza configuracion entre desarrolladores
5. **`.secrets` en `.gitignore`**: Nunca committear secretos
6. **Job especifico**: `act -j quality-gates` para feedback rapido
7. **Skip steps locales**: `if: ${{ !env.ACT }}` para steps no locales (deploy, notificacion)
8. **`--verbose` para debug**: Muestra detalles de Docker API calls
9. **Artefactos locales**: `--artifact-server-path ./tmp/artifacts` para debugging
