# test_runner

Ejecuta tests para uno o todos los módulos del proyecto via Docker.

## Uso

```bash
python devtools/run.py test_runner [flags]
```

## Flags

| Flag | Descripción | Default |
| --- | --- | --- |
| `--module=<name>` | Módulo a testear (`server`, `dashboard`, `landing`, `devtools`) | todos los módulos con tests |
| `--type=<type>` | Tipo de test (`unit`, `feature`, `integration`, `coverage`, `typecheck`, `all`) | `all` |
| `--git-mode=<mode>` | Filtrar por estado git (`changed`, `staged`, `unstaged`, `unmerged`, `all`) | sin filtro |
| `--env=<env>` | Docker environment (`local`, `dev`, `test`) | local |
| `--verbose` | Informacion detallada | false |
| `--quiet` | Suprimir output en exito | false |
| `--screenshots` | Generar screenshots durante feature (solo `dashboard`/`landing`) | false |
| `--ui-review` | Revisar screenshots con Gemini CLI tras ejecución | false |
| `--skip-empty` | Saltar si no hay archivos (con git-mode) | true |

## Test types por módulo

| Módulo | Tipos disponibles |
| --- | --- |
| server | unit, feature, integration, coverage |
| dashboard | unit, feature, coverage, typecheck |
| landing | unit, feature, coverage, typecheck |
| devtools | unit |

> Mayo 2026: el módulo `e2e` y el tipo `--type=e2e` fueron eliminados.
> Cada producto (dashboard, landing, server) tiene su propio
> `--type=feature` (BDD-style: Playwright para frontend, DRF APIClient +
> seed_db para server).

## Ejemplos

```bash
# Suite completa (todos los módulos)
python devtools/run.py test_runner

# Server: coverage per-file >= 80%
python devtools/run.py test_runner --module=server --type=coverage --verbose

# Dashboard: solo typecheck
python devtools/run.py test_runner --module=dashboard --type=typecheck

# Feature tests del dashboard (Playwright Chromium + WebKit)
python devtools/run.py test_runner --module=dashboard --type=feature

# Solo archivos cambiados
python devtools/run.py test_runner --git-mode=changed

# Tests de archivos staged + per-file coverage
python devtools/run.py test_runner --git-mode=staged
```

## Requisitos

- Docker debe estar corriendo (`python devtools/run.py docker up --env=local`)
- Para `--type=feature` con `--module=dashboard|landing`: los containers
  `dashboard-feature` y `landing-feature` se levantan on-demand bajo el
  profile `feature`. Primera invocacion tarda ~3-5 min instalando browsers
  (Chromium + WebKit). Timeout configurable via env var
  `FEATURE_READY_TIMEOUT` (default 600s).

## También disponible via test_runner

```bash
python devtools/run.py test_runner --module=server --type=unit
python devtools/run.py test_runner --module=dashboard --type=coverage
python devtools/run.py test_runner --module=landing --type=typecheck
```
