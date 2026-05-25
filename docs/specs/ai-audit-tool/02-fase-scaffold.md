# 02 - Fase scaffold

> Skeleton del paquete `devtools/ai_audit/` + dependencia Playwright +
> entradas en `.gitignore`. NO incluye logica de scrapers, auth, ni
> reporte — solo estructura + flags parser + catalog (testeable
> aislado).

[< 01 Contexto](01-contexto-y-decision.md) | [03 Fase auth >](03-fase-auth.md)

## Alcance

- Crear arbol de directorios del paquete (con `__init__.py` vacios).
- Agregar `playwright` a `devtools/pyproject.toml`; regenerar
  `uv.lock`.
- Implementar `flags.py` (parser + validacion) + tests.
- Implementar `catalog.py` (niche x env -> URL) + tests.
- Implementar `main.py` minimal (router de subcomandos; bodies son
  `raise NotImplementedError`).
- Agregar `tmp/ai-audit/` y `docker/env/dev-cli/ai-audit/` al
  `.gitignore` raiz.

## AC referenciados

- AC-7 (flags invalidos -> exit 2 con mensaje claro)
- AC-2 parcial (resolver niches -> URLs)

## Tareas atomicas

### T-2.1 Skeleton + pyproject + .gitignore

- Crear `devtools/ai_audit/__init__.py`,
  `devtools/ai_audit/main.py`, `devtools/ai_audit/flags.py`,
  `devtools/ai_audit/catalog.py`, `devtools/ai_audit/README.md`.
- Crear `devtools/ai_audit/tools/__init__.py` y
  `devtools/ai_audit/tools/base.py` (stubs).
- `uv add playwright --project devtools`.
- `.gitignore`: agregar 2 patterns.

**Verify**: `python -m compileall -q devtools/ai_audit` + `git check-ignore tmp/ai-audit/x docker/env/dev-cli/ai-audit/x.json` (deben matchear).

### T-2.2 flags.py

Parsing soportado:

- subcomandos: `(default)`, `setup`, `report`
- flags globales: `--env=<dev|stage|prod>` (default prod),
  `--niches=<csv>` (default = los 6), `--targets=<csv niche:/path>`,
  `--tools=<csv>` (default = las 4)
- setup-only: `--tool=<X>` (obligatorio), `--check-only` (bool)
- report-only: `--snapshot=<path>` (obligatorio)

Validacion:

- `--env` valido contra enum.
- `--niches` subset de los 6 conocidos.
- `--targets` formato `niche:/path` (`/path` debe empezar con `/`).
- `--tools` subset de las 4 conocidas.
- subcomando `setup` requiere `--tool`; subcomando `report` requiere
  `--snapshot`.

Tests (`test_flags.py`):

- Given `[]`, When parse, Then default subcomando + prod + 6 niches + 4 tools [AC-7]
- Given `['--tools=foo']`, When parse, Then exit 2 + mensaje `unknown tool: foo` [AC-7]
- Given `['--env=qa']`, When parse, Then exit 2 + mensaje `invalid env: qa` [AC-7]
- Given `['--niches=hub,unknown']`, When parse, Then exit 2 + mensaje `unknown niches: unknown` [AC-7]
- Given `['--targets=hub:projects']`, When parse, Then exit 2 + mensaje `path must start with /` [AC-7]
- Given `['setup']` sin `--tool`, When parse, Then exit 2 + mensaje `setup requires --tool` [AC-7]
- Given `['setup', '--tool=ahrefs']`, When parse, Then dict bien formado [AC-1]
- Given `['report', '--snapshot=/x/y.json']`, When parse, Then dict bien formado [AC-5]

**Verify**: `cd devtools && uv run pytest tests/unit/src/ai_audit/test_flags.py -v`.

### T-2.3 catalog.py

Mapea `(env, niche)` a URL absoluta. Reusa los hostnames del
portfolio:

```python
NICHES = ('generic', 'hub', 'fintech', 'architect', 'leader', 'vibe')

def resolve_url(env: str, niche: str, path: str = '/') -> str:
    """Resuelve URL absoluta segun env."""
    # prod: generic = the-full-stack.com; resto = {niche}.portfolio.the-full-stack.com
    # stage: {niche}.portfolio.stage.the-full-stack.com  (generic incluido)
    # dev:   {niche}.portfolio.dev.the-full-stack.com    (generic incluido)
```

Tests (`test_catalog.py`):

- Given env=prod niche=generic, When resolve_url('/'), Then `https://the-full-stack.com/` [AC-2]
- Given env=prod niche=hub, When resolve_url('/'), Then `https://hub.portfolio.the-full-stack.com/` [AC-2]
- Given env=stage niche=generic, When resolve_url('/projects'), Then `https://generic.portfolio.stage.the-full-stack.com/projects` [AC-2]
- Given env=dev niche=fintech, When resolve_url('/'), Then `https://fintech.portfolio.dev.the-full-stack.com/` [AC-2]

**Verify**: `cd devtools && uv run pytest tests/unit/src/ai_audit/test_catalog.py -v`.

### T-2.4 main.py minimal

Solo routing:

```python
def main(flags: dict) -> int:
    subcommand = flags['subcommand']
    if subcommand == 'setup':
        raise NotImplementedError('see fase 03')
    elif subcommand == 'report':
        raise NotImplementedError('see fase 05')
    else:
        raise NotImplementedError('see fase 06')
```

**Verify**: `python -m compileall -q devtools/ai_audit/main.py` + `cd devtools && uv run pytest tests/unit/src/ai_audit/` debe pasar.

## Done

- [ ] T-2.1 skeleton + deps + gitignore: compileall ok + ignore matchea
- [ ] T-2.2 flags + tests: 8/8 pasan, coverage >= 80%
- [ ] T-2.3 catalog + tests: 4/4 pasan, coverage >= 80%
- [ ] T-2.4 main minimal: compila + routing testeable
- [ ] Commit: `feat(devtools): scaffold devtools/ai_audit (flags + catalog + skeleton)`

[< 01 Contexto](01-contexto-y-decision.md) | [03 Fase auth >](03-fase-auth.md)
