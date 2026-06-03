# test_runner

Ejecuta unit + coverage + typecheck para uno o todos los módulos del
proyecto via Docker (apps Astro / packages con Vitest, server con pytest,
devtools con pytest en el host).

## Uso

```bash
python devtools/run.py test_runner [flags]
```

## Flags

| Flag | Descripción | Default |
| --- | --- | --- |
| `--module=<name>` | Módulo a testear (apps Astro, `pkg-*`, `server`, `devtools`) | todos los módulos con tests |
| `--type=<type>` | Tipo de test (`unit`, `coverage`, `typecheck`, `all`) | `all` |
| `--git-mode=<mode>` | Filtrar por estado git (`changed`, `staged`, `unstaged`, `unmerged`, `all`) | sin filtro |
| `--env=<env>` | Docker environment (`local`, `dev`, `test`) | local |
| `--verbose` | Informacion detallada | false |
| `--quiet` | Suprimir output en exito | false |
| `--skip-empty` | Saltar si no hay archivos (con git-mode) | true |

## Test types por módulo

| Módulo | Tipos disponibles |
| --- | --- |
| hub / generic / fintech / architect / leader / vibe | unit, coverage, typecheck |
| pkg-app-shared / pkg-content / pkg-cv-pdf / pkg-seo / pkg-ui | unit, coverage |
| server | unit |
| devtools | unit |

> Junio 2026: los E2E del portfolio (Playwright) ya no viven en
> test_runner. Los módulos/tipos `feature`, `e2e` y `tests` fueron
> eliminados (junto con los flags playwright-only `--project`, `--shard`,
> `--shard-total`, `--fail-on-flaky`, `--screenshots`, `--ui-review`) y se
> corren con el comando dedicado:
>
> ```bash
> python devtools/run.py e2e --module=<api|admin|app> --env=dev
> ```

## Ejemplos

```bash
# Suite completa (todos los módulos)
python devtools/run.py test_runner

# Server: solo unit tests
python devtools/run.py test_runner --module=server --type=unit --verbose

# App Astro: solo typecheck
python devtools/run.py test_runner --module=generic --type=typecheck

# Package: unit + coverage
python devtools/run.py test_runner --module=pkg-content --type=coverage

# Solo archivos cambiados
python devtools/run.py test_runner --git-mode=changed

# Tests de archivos staged + per-file coverage
python devtools/run.py test_runner --git-mode=staged
```

## Requisitos

- Docker debe estar corriendo (`python devtools/run.py docker up --env=local`)
  para los módulos `server` y las apps Astro / packages.
- `devtools` corre en el host (Python 3.14 via `devtools/.venv`) y NO
  depende de Docker.
