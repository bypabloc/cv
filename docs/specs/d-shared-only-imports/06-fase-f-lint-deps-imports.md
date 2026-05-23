# Fase F — Extender lint-deps con check de imports prohibidos

> `serverless lint-deps` ya valida dedup D-3 sobre `pyproject.toml`. Esta
> fase agrega un check adicional: escanea `services/*/core/**/*.py` y
> falla si encuentra imports directos a los 7 paquetes prohibidos. Cero
> exenciones en `core/`. tests/ del service NO se escanean.

## Contexto / Problema

- `devtools/serverless/dep_validator.py` implementa `cmd_lint_deps` que
  valida la regla D-3 (un service no declara deps que ya aporta el cierre
  de `shared/`).
- Despues de Fase E, los services NO declaran pydantic/boto3/etc. en su
  pyproject.toml — el check D-3 pasa.
- Pero un dev futuro puede agregar `from pydantic import BaseModel` en un
  archivo nuevo de `core/` sin agregar la dep al pyproject (pydantic ya
  viene transitivo), y el check actual NO lo detecta.

## Solucion

### F.1 — Helper de escaneo en devtools

Crear `devtools/serverless/import_validator.py`:

```python
"""@module devtools.serverless.import_validator — check de imports en core/.

Escanea services/*/core/**/*.py y reporta cualquier import directo a los
paquetes que tienen un portador shared. Forma parte del comando
`serverless lint-deps`.
"""
from __future__ import annotations

import ast
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


# Paquetes raiz que NO deben importarse directamente en services/*/core/.
# El service debe importarlos desde shared.* (que actua como portador).
_FORBIDDEN_ROOTS = frozenset({
    'pydantic',
    'pydantic_settings',
    'sqlalchemy',
    'alembic',
    'psycopg',
    'boto3',
    'botocore',
    'aws_lambda_powertools',
})


@dataclass(frozen=True)
class ForbiddenImport:
    path: Path
    lineno: int
    statement: str
    package: str


def _root_of(module: str) -> str:
    """Devuelve el paquete raiz de un dotted module ('a.b.c' -> 'a')."""
    return module.split('.', 1)[0]


def _iter_imports(tree: ast.Module) -> Iterator[tuple[int, str, str]]:
    """Itera (lineno, statement, root_module) de cada import del AST."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = _root_of(alias.name)
                yield node.lineno, f'import {alias.name}', root
        elif isinstance(node, ast.ImportFrom):
            # `from . import x` -> module=None; lo ignoramos (relativo).
            if node.module is None or node.level > 0:
                continue
            root = _root_of(node.module)
            yield node.lineno, f'from {node.module} import ...', root


def scan_file(path: Path) -> list[ForbiddenImport]:
    """Escanea un .py y devuelve los imports prohibidos encontrados."""
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except SyntaxError:
        return []  # archivos con sintaxis invalida los reporta otro check
    return [
        ForbiddenImport(path, lineno, statement, root)
        for lineno, statement, root in _iter_imports(tree)
        if root in _FORBIDDEN_ROOTS
    ]


def scan_lambda_core(lambda_root: Path) -> list[ForbiddenImport]:
    """Escanea services/<lambda>/core/**/*.py."""
    core = lambda_root / 'core'
    if not core.is_dir():
        return []
    violations: list[ForbiddenImport] = []
    for py in sorted(core.rglob('*.py')):
        violations.extend(scan_file(py))
    return violations
```

### F.2 — Integracion en `dep_validator.py`

Editar `devtools/serverless/dep_validator.py` para que `cmd_lint_deps`
ejecute AMBOS checks:

```python
from devtools.serverless.import_validator import scan_lambda_core, ForbiddenImport


def cmd_lint_deps(flags: dict) -> int:
    targets = _resolve_targets(flags)  # ya existe
    dedup_failures = []
    import_failures: list[ForbiddenImport] = []

    for lambda_root in targets:
        # check 1: dedup existente
        if not _validate_deps_dedup(lambda_root):
            dedup_failures.append(lambda_root)
        # check 2: imports prohibidos en core/ (nuevo)
        import_failures.extend(scan_lambda_core(lambda_root))

    if dedup_failures:
        _print_dedup_report(dedup_failures)
    if import_failures:
        _print_import_report(import_failures)

    return 0 if not (dedup_failures or import_failures) else 1
```

Output esperado para fallos de import (UI similar al output de dedup):

```text
[FAIL] cv/core/models/cv.py:1
       from pydantic import ...
       paquete prohibido directo: 'pydantic'. Importa desde 'shared.core'.

[FAIL] db/core/services/seed_service.py:67
       from sqlalchemy import ...
       paquete prohibido directo: 'sqlalchemy'. Importa desde 'shared.db'.
```

### F.3 — Tests del check

Crear en `devtools/tests/serverless/test_import_validator.py`:

- `test_scan_file_detects_pydantic_import` — Given un .py con
  `from pydantic import BaseModel`, When scan_file, Then la lista
  contiene un `ForbiddenImport(package='pydantic', lineno=1)`.
- `test_scan_file_ignores_shared_imports` — Given `from shared.core
  import BaseModel`, When scan_file, Then lista vacia.
- `test_scan_file_ignores_stdlib` — Given `import os, json`, Then lista
  vacia.
- `test_scan_file_detects_boto3_dynamodb_types` — Given `from
  boto3.dynamodb.types import TypeDeserializer`, Then detecta `boto3`.
- `test_scan_lambda_core_walks_recursively` — Given tree
  `core/services/x.py` con import prohibido y `core/models/y.py` sin,
  Then scan_lambda_core devuelve solo el de x.py.
- `test_scan_lambda_core_skips_tests_dir` — Given tree con `tests/x.py`
  importando pydantic, Then scan_lambda_core no lo reporta (solo escanea
  `core/`).
- `test_scan_file_handles_syntax_error_gracefully` — Given .py con
  SyntaxError, Then devuelve lista vacia (no lanza).
- `test_scan_file_ignores_relative_imports` — Given `from . import x`,
  Then no se reporta (relativo).

Cada test: un archivo, BDD docstring, AAA en el cuerpo, assert exacto.

### F.4 — CI

`.github/workflows/ci.yml` (y los hooks pre-push) ya invocan
`serverless lint-deps`. Como el comando ahora ejecuta los 2 checks juntos,
no hay cambios de CI — la regresion futura se detecta automaticamente.

## Archivos afectados

### Crear

- `devtools/serverless/import_validator.py` — modulo nuevo.
  - Verificar: `python devtools/run.py test_runner --module=devtools --type=unit -- -k import_validator`.
- `devtools/tests/serverless/test_import_validator.py` (8 tests).

### Modificar

- `devtools/serverless/dep_validator.py` — integra el segundo check en `cmd_lint_deps`.
  - Verificar: `python devtools/run.py serverless lint-deps` (debe pasar tras Fase E).

## Criterios de aceptacion

- **AC-F1**: Given un archivo `services/foo/core/x.py` con `from pydantic
  import BaseModel`, When ejecuto `serverless lint-deps --lambda=foo`,
  Then exit 1 y el reporte muestra el archivo + linea + paquete.
- **AC-F2**: Given los 5 services migrados (Fase E completa), When ejecuto
  `serverless lint-deps`, Then exit 0.
- **AC-F3**: Given un archivo `services/foo/tests/x.py` con `from pydantic
  import BaseModel`, When ejecuto `serverless lint-deps --lambda=foo`,
  Then exit 0 (tests/ exento del check).
- **AC-F4**: Given un archivo `services/foo/core/x.py` con `from shared.core
  import BaseModel`, When ejecuto el escaneo, Then exit 0 (shared.* OK).
- **AC-F5**: Given un .py con SyntaxError, When scan_file lo procesa, Then
  retorna lista vacia (no lanza la excepcion).

## Verificacion

```bash
python devtools/run.py test_runner --module=devtools --type=unit
python devtools/run.py serverless lint-deps
```

## Commit

```text
feat(devtools/serverless): lint-deps escanea imports prohibidos en core/

- Nuevo modulo devtools/serverless/import_validator.py con scan_file y
  scan_lambda_core; detecta imports directos a pydantic, sqlalchemy,
  alembic, psycopg, boto3, botocore, aws_lambda_powertools en
  services/*/core/**/*.py
- dep_validator.cmd_lint_deps ahora ejecuta ambos checks (dedup D-3 +
  imports prohibidos) en una sola pasada; exit 1 si cualquiera falla
- 8 tests unit del scanner: detect pydantic, ignore shared, ignore stdlib,
  boto3.dynamodb.types, walk recursivo, skip tests/, SyntaxError graceful,
  ignore imports relativos
- core/ del service es zona estricta; tests/ exento (mocks de pydantic
  ok en tests)
```
