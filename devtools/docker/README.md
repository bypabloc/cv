# Docker CLI

> Gestion de Docker multi-ambiente para portfolio.

## Uso

```bash
python devtools/run.py docker <command> [--env=local] [flags...]
```

## Ambientes

| Ambiente | Descripcion | Puerto (default) |
| -------- | ----------- | ---------------- |
| local | Desarrollo con hot reload (default) | 9979 |
| dev | Desarrollo remoto (code baked) | 9978 |
| test | Testing aislado | 9977 |
| prod | Produccion con Gunicorn | 80 |

> El puerto se override via `PROXY_PORT` en `docker/env/.<env>`.

## Comandos

### Lifecycle

| Comando | Descripcion | Flags |
| ------- | ----------- | ----- |
| up | Levantar servicios | `--build`, `--detach` (default), `--service=NAME`, `--profile=NAME` |
| down | Detener servicios | `--volumes` (eliminar datos) |
| build | Construir imagenes | `--no-cache`, `--service=NAME`, `--profile=NAME` |
| rebuild | Clean rebuild | `--service=NAME`, `--profile=NAME` |
| logs | Ver logs | --tail=50, --follow / -w |
| shell | Bash en server | |
| exec | Ejecutar comando | --target=server |
| ps | Listar containers | |
| restart | Reiniciar servicios | |
| refresh | Down + clean + up | --keep-volumes, --skip-cache |

#### Service-scoped operations

`--service=NAME` limita la operacion a un solo container (mas rapido que rebuild completo). El profile se auto-resuelve si el servicio esta gated bajo uno (ej: `e2e` bajo `profiles: [e2e]`).

`--profile=NAME` se necesita SOLO para servicios on-demand (ej: levantar
manualmente el servicio `e2e` requiere `--profile=e2e`).

Ejemplos:

```bash
# Rebuild solo el container feature (con --no-cache + auto-profile)
python devtools/run.py docker rebuild --env=local --service=dashboard-feature

# Build solo la imagen de dashboard
python devtools/run.py docker build --env=local --service=dashboard

# Levantar el servicio feature (on-demand, profile auto-resuelto)
python devtools/run.py docker up --env=local --service=dashboard-feature

# Levantar todos los servicios incluyendo profile feature
python devtools/run.py docker up --env=local --profile=feature
```

### Django

| Comando | Descripcion | Flags |
| ------- | ----------- | ----- |
| migrate | Ejecutar migraciones | |
| makemigrations | Generar migraciones | |
| createsuperuser | Crear admin (non-interactive, lee env vars) | |
| manage | Pass-through a manage.py | `<subcommand> [-- --flag]` |

> `manage` y `exec` son pass-through: para reenviar flags al subproceso,
> usa el separador POSIX `--`. Ej: `docker manage migrate -- --plan` o
> `docker exec --target=dashboard -- pnpm install`. Sin `--` el validador
> sugiere el ejemplo correcto.

### Calidad

| Comando | Descripcion | Flags |
| ------- | ----------- | ----- |
| lint | Lint (Ruff/Biome) | `--module=server\|devtools\|dashboard\|landing` (default: `server`) |
| lint-fix | Lint con auto-fix | `--module=server\|devtools\|dashboard\|landing` |
| format | Format (Ruff/Biome) | `--module=server\|devtools\|dashboard\|landing` |

> El subcomando `test` fue removido del CLI en 2026-05. Para ejecutar tests
> usa el script unificado: `python devtools/run.py test_runner [flags]`.
> Si invocas `docker test` veras un mensaje de migracion con las
> equivalencias para tus comandos.

### Base de datos

| Comando | Descripcion | Flags |
| ------- | ----------- | ----- |
| db-shell | psql interactivo | |
| db-tables | Listar tablas | `--output=text\|json` |
| db-describe | Describir tabla | `<table_name>` (posicional) |
| db-count | Conteo de registros por tabla | `--output=text\|json` |
| db-seed | Cargar fixtures | `--clear`, `--only=<app>`, `--dry-run` |
| db-reset | Reset completo | `--no-seed`, `--no-superuser`, `--dry-run` |

`--output=json` emite un documento parseable directo con `jq` o `json.load(sys.stdin)`. Disponible tambien en `ps` y `cache-status`.

### Setup

| Comando | Descripcion | Flags |
| ------- | ----------- | ----- |
| setup | Setup inicial completo | --no-seed, --no-superuser |
| clean | Eliminar todo (containers, images, volumes) | |
| help | Mostrar ayuda | |

### Cache

| Comando | Descripcion |
| ------- | ----------- |
| cache-clear-all | Limpiar __pycache__ |
| cache-status | Estado de cache |

## Ejemplos

```bash
# Setup inicial
python devtools/run.py docker setup --env=local

# Desarrollo diario
python devtools/run.py docker up --env=local
python devtools/run.py docker logs --follow
python devtools/run.py docker shell

# Testing
python devtools/run.py test_runner --module=server --type=unit --verbose
python devtools/run.py test_runner --module=server --type=integration

# Database
python devtools/run.py docker db-seed --env=local --clear
python devtools/run.py docker db-count

# Produccion
python devtools/run.py docker build --env=prod --no-cache
python devtools/run.py docker up --env=prod
```

## Introspeccion (machine-readable)

Para agentes y scripts: cada comando expone su contrato via `describe()`.

```bash
# Inventario de comandos (29) con flags relevantes y flags destructive/deprecated
python devtools/run.py docker --list-commands --output=json

# Solo flags top-level del subcomando docker
python devtools/run.py docker --list-flags --output=json

# Flag JSON disponible en: ps, db-tables, db-count, cache-status
python devtools/run.py docker ps --env=local --output=json | jq '.[0].Name'
python devtools/run.py docker db-count --env=local --output=json | jq
```

Para discutir el contrato del separador POSIX `--` y otros system flags
(`_passthrough`, `_invoked_from`), ver `devtools/utils/flags_to_dict.py`.
