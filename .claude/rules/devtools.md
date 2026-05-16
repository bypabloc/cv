---
description: "Estandares para scripts de desarrollo en devtools/: estructura de scripts, flags pattern, ruff config autocontenido"
globs: "devtools/**/*.py"
---

# Devtools Development Standards

> Reglas para scripts de desarrollo en devtools/.

## Estructura

- Entry point unico: `devtools/run.py` (plugin loader dinamico)
- Cada script es un paquete: `devtools/<nombre>/`
- Archivos obligatorios por script: `main.py` (logica) + `flags.py` (validacion) + `README.md`
- Utilidades compartidas en `devtools/shared/` y `devtools/utils/`
- Scripts disponibles: `scan`, `docker`, `test_runner`, `verify`, `hooks`,
  `e2e`, `init`, `upgrade_deps`
- Modulos por script max 300 lineas — partir por dominio cuando crece
  (ver `docker/`, `scan/`, `test_runner/` como ejemplo)

## API: posicional vs flags

Convencion fija para que el CLI sea predecible:

- **Scripts con multiples comandos discretos** (`docker` y futuros similares)
  toman comando posicional: `docker up`, `docker shell`. El comando NO se
  pasa como `--command=...`.
- **Scripts mono-comando con parametrizacion** (`scan`, `test_runner`,
  `verify`, `upgrade_deps`, `init`, `hooks`, `e2e`) usan SOLO flags. No
  exponen subcomandos: el script es la unidad. Ej: `test_runner
  --module=pkg-content --type=unit`.

## Comando unico para tests

Tests se corren via `python devtools/run.py test_runner [flags]`. El viejo
`docker test` fue removido en 2026-05 (Fase 3 del refactor CLI). Si alguien
lo invoca, `docker test` imprime un mensaje de migracion con equivalencias
y exit 1. NUNCA se vuelve a anadir como atajo: una sola fuente de verdad.

## Convenciones de codigo

- Python 3.14 (se ejecuta en local via `devtools/.venv`, NO en Docker)
- devtools es un CLI Python autocontenido: sin acoplamiento al resto del
  monorepo, sin dependencias de las apps Astro ni de sus toolchains
- Ruff config propio: `devtools/ruff.toml` (autocontenido, sin extends, autodetectado cuando cwd=`/app/devtools/`)
- Dependencias propias en `devtools/pyproject.toml` + `devtools/uv.lock` (gestionado por uv)
- Bootstrap automatico: `devtools/run.py` ejecuta `uv sync --frozen --project devtools` la primera vez (o cuando el lockfile cambia) y se re-exec en `devtools/.venv/bin/python`
- Type hints obligatorios en funciones publicas

## Ruff config (devtools-specific)

`devtools/ruff.toml` es un archivo autocontenido (sin `extend`). Contiene
todas las reglas comunes mas estas particularidades de devtools:

- `src = ["."]` (cwd es la raiz del modulo)
- `per-file-target-version`: `devtools/run.py` y `.git-hooks/**/*.py` pinneados a `py313` (corren en Python del shell ANTES del re-exec a Python 3.14 del `.venv`)
- Ignorados globales adicionales: `TRY003` (CLI tools usan mensajes descriptivos en excepciones — son la interfaz de usuario)
- Per-file ignores: `**/*.py` ignora `T20` (`print()` es la interfaz de CLI) y `F401` (imports para re-export en `__init__.py` es comun)
- Tests: `devtools/tests/**/*.py` ignora `S101`, `ANN001`/`201`/`202`, `PLR2004` (magic values en asserts), `INP001` (tests no necesitan `__init__.py`)
- isort known-first-party: `scan`, `docker`, `test_runner`
- isort known-third-party: `git` (GitPython)

## Patron flags.py

- Cada script define sus flags en `flags.py` con validacion
- Retorna un dict tipado con los flags parseados
- Validacion de combinaciones invalidas antes de ejecutar

## Patron main.py

- Funcion `main(flags: dict)` como entry point
- Logging con modulo `logging`, nunca `print()` (excepto en CLI output donde `T20` esta ignorado)
- Exit codes: 0 (ok), 1 (error de usuario), 2 (error interno)

## Testing

- Tests en `devtools/tests/` (si aplican)
- Testear logica pura: parsing de flags, validaciones, transformaciones
- Coverage y formatter obligatorios
