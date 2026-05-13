# scan

Lista archivos del repo con filtros git-aware y, opcionalmente, su
contenido. Es la pieza que usan los git-hooks (`.git-hooks/_common.py`)
para clasificar archivos por módulo y purpose, y la que usa
`test_runner --git-mode=...` para mapear cambios a tests.

## Uso

```bash
python devtools/run.py scan [flags]
```

## Flags principales

| Flag | Descripción | Default |
|------|-------------|---------|
| `--git-mode=<mode>` | `changed`, `staged`, `unstaged`, `stash`, `unmerged`, `all` | none |
| `--module=<name>` | Limita a `server`, `dashboard`, `landing`, `devtools` | none |
| `--purpose=<name>` | `conformance` o `coverage` (aplica excludes especificos) | none |
| `--only-extensión=<ext>` | Filtra por extensión (ej: `py`, `ts`) | [] |
| `--excludes-extensión=<ext>` | Excluye extensiones | [] |
| `--only-list` | Output `;`-separado (machine-readable, para pipe) | false |
| `--only-folders-root` | Solo lista carpetas raíz | false |
| `--include-ignored` | Incluye archivos en .gitignore | false |
| `--include-deleted` | Incluye archivos eliminados (modo unmerged) | false |
| `--exclude-empty` | Omite archivos vacíos | false |
| `--ignore-patterns=<glob>` | Patterns adicionales (separados por pipe) | [] |

## Ejemplos

```bash
# Archivos Python staged (lista pura para piping)
python devtools/run.py scan --git-mode=staged --module=server --only-list

# Estructura completa server con contenido
python devtools/run.py scan --module=server --git-mode=all

# Archivos cubiertos por coverage en server (purpose aplica excludes)
python devtools/run.py scan --module=server --purpose=coverage \
    --git-mode=changed --only-list

# No mergeados vs rama base, solo Python (revisión pre-PR)
python devtools/run.py scan --git-mode=unmerged --only-extensión=py

# Carpetas raíz del proyecto (utilidad para descubrir módulos)
python devtools/run.py scan --only-folders-root
```

## Modos git

- **changed**: staged + unstaged + untracked (default operativo)
- **staged**: archivos en staging area
- **unstaged**: archivos modificados no staged
- **stash**: archivos del stash mas reciente
- **unmerged**: archivos no mergeados vs rama base detectada (main/master/dev)
- **all**: todos los modos separados por categoria en el output

## Modules y purposes

Definidos en `devtools/scan/modules.py`:

- **modules**: `server`, `dashboard`, `landing`, `devtools` — cada uno tiene
  extensions, exclude_patterns y opcionalmente `ruff_config`. Limita el
  scan a archivos bajo el root del módulo.
- **purposes**: `conformance` (lint/format) y `coverage` (tests con
  coverage). Cada uno aplica excludes adicionales (ej: coverage excluye
  `__init__.py`, `migrations/`, etc.).

## Quien lo usa

- `.git-hooks/_common.py` — clasifica staged files para correr lint/coverage
  por módulo
- `devtools/test_runner` — mapea archivos cambiados a tests via
  path mirroring + per-file coverage
- Manual / CI — para inspeccionar la estructura del proyecto

## Estructura interna (post Fase 2)

- `main.py` — entry point thin (orquesta + imprime)
- `ignore.py` — gitignore + glob/regex matching + should_exclude_file
- `git_query.py` — git ls-files, base branch, modes, deleted, content from git
- `files.py` — get_file_content + get_file_dates (filesystem)
- `structure.py` — assembler que produce el dict final
- `display.py` — `_display_list_mode` + `_display_detailed_mode`
- `flags.py` — validación de flags (incluye `describe()` para introspeccion)
- `modules.py` — registry de módulos y purposes
