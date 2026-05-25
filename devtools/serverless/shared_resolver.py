"""Resolucion del cierre de subpaquetes de `shared/` que usa un lambda.

La libreria comun `serverless/lambda/shared/` esta organizada en subpaquetes por
dominio (`core`, `aws`, `observability`, `http`, `db`, `dynamodb`,
`cache`, `rate_limit`). Cada subpaquete declara, en su propio
`pyproject.toml`:

  - `[project.dependencies]`        — deps externas (PyPI) que necesita.
  - `[tool.shared] internal-deps`   — otros subpaquetes de `shared/` de
                                       los que depende.

Este modulo escanea el AST del codigo de un lambda (`core/**/*.py`),
detecta los `from shared.<subpaquete>` que usa, y resuelve el **cierre
transitivo**: si el lambda usa `shared.http` y `http` declara
`internal-deps = ['core', 'aws']`, el cierre incluye `core` y `aws`.

El resultado permite a `vendoring.py` copiar SOLO los subpaquetes
necesarios y al empaquetado sumar SOLO las deps externas de ese
conjunto. Un lambda que no usa `shared.db` no arrastra `sqlalchemy`.

devtools corre en Python 3.14 (`devtools/.venv`); `tomllib` es stdlib.
"""

from __future__ import annotations

import ast
from pathlib import Path
import tomllib


# Raiz del backend serverless del portfolio.
_SERVERLESS_DIR = Path(__file__).resolve().parents[2] / 'serverless'

# Fuente de verdad de la libreria comun (serverless/lambda/shared/).
_SHARED_SOURCE = _SERVERLESS_DIR / 'lambda' / 'shared'

# Nombre del paquete raiz de la libreria comun en los imports.
_SHARED_ROOT = 'shared'


class SharedResolverError(RuntimeError):
    """Error al resolver el cierre de subpaquetes de `shared/`."""


def shared_root() -> Path:
    """Devuelve el path de la fuente maestra `serverless/lambda/shared/`.

    Raises
    ------
    SharedResolverError
        Si `serverless/lambda/shared/` no existe.
    """
    if not _SHARED_SOURCE.is_dir():
        raise SharedResolverError(
            f'No existe la libreria comun en {_SHARED_SOURCE}.',
        )
    return _SHARED_SOURCE


def available_subpackages(*, shared_dir: Path | None = None) -> set[str]:
    """Devuelve el set de subpaquetes presentes en `shared/`.

    Un subpaquete es un directorio hijo de `shared/` con `__init__.py`.

    Parameters
    ----------
    shared_dir : Path | None
        Override de la raiz de `shared/` (para tests). Default: la real.
    """
    root = shared_dir if shared_dir is not None else shared_root()
    return {
        child.name
        for child in root.iterdir()
        if child.is_dir() and (child / '__init__.py').is_file()
    }


def scan_imports(source_root: Path) -> set[str]:
    """Escanea `source_root/**/*.py` y devuelve los subpaquetes de
    `shared/` importados de forma directa.

    Detecta `from shared.<subpaquete>...` e `import shared.<subpaquete>`.
    NO resuelve transitividad: solo lo que el codigo escanea importa
    explicitamente.

    Parameters
    ----------
    source_root : Path
        Directorio a escanear (tipicamente `<lambda>/core/`).

    Returns
    -------
    set[str]
        Nombres de subpaquetes de `shared/` importados directamente.

    Raises
    ------
    SharedResolverError
        Si un archivo `.py` tiene un error de sintaxis.
    """
    found: set[str] = set()
    for py_file in sorted(source_root.rglob('*.py')):
        try:
            tree = ast.parse(py_file.read_text(encoding='utf-8'))
        except SyntaxError as exc:
            raise SharedResolverError(
                f'Error de sintaxis en {py_file}: {exc}',
            ) from exc
        for node in ast.walk(tree):
            found |= _subpackages_in_node(node)
    return found


def _subpackages_in_node(node: ast.AST) -> set[str]:
    """Extrae los subpaquetes de `shared/` referenciados en un nodo AST.

    Reconoce dos formas:
      - `from shared.<sub>[...] import X`  (ImportFrom, level 0)
      - `import shared.<sub>[...]`         (Import)
    """
    if isinstance(node, ast.ImportFrom):
        if node.level == 0 and node.module:
            parts = node.module.split('.')
            if parts[0] == _SHARED_ROOT and len(parts) >= 2:
                return {parts[1]}
        return set()
    if isinstance(node, ast.Import):
        found: set[str] = set()
        for alias in node.names:
            parts = alias.name.split('.')
            if parts[0] == _SHARED_ROOT and len(parts) >= 2:
                found.add(parts[1])
        return found
    return set()


def _read_manifest(
    subpackage: str,
    *,
    shared_dir: Path,
) -> tuple[list[str], list[str]]:
    """Lee el `pyproject.toml` de un subpaquete de `shared/`.

    Returns
    -------
    tuple[list[str], list[str]]
        `(external_deps, internal_deps)` — deps PyPI y subpaquetes
        internos declarados por ese subpaquete.

    Raises
    ------
    SharedResolverError
        Si el subpaquete no tiene `pyproject.toml` o esta malformado.
    """
    manifest = shared_dir / subpackage / 'pyproject.toml'
    if not manifest.is_file():
        raise SharedResolverError(
            f'El subpaquete shared/{subpackage} no tiene pyproject.toml.',
        )
    try:
        data = tomllib.loads(manifest.read_text(encoding='utf-8'))
    except tomllib.TOMLDecodeError as exc:
        raise SharedResolverError(
            f'pyproject.toml invalido en shared/{subpackage}: {exc}',
        ) from exc
    external = list(data.get('project', {}).get('dependencies', []))
    internal = list(
        data.get('tool', {}).get('shared', {}).get('internal-deps', []),
    )
    return external, internal


def resolve_closure(
    direct: set[str],
    *,
    shared_dir: Path | None = None,
) -> set[str]:
    """Resuelve el cierre transitivo de subpaquetes de `shared/`.

    Dado el set de subpaquetes importados directamente por un lambda,
    expande recursivamente las `internal-deps` declaradas en cada
    `pyproject.toml` hasta alcanzar el punto fijo.

    Parameters
    ----------
    direct : set[str]
        Subpaquetes importados directamente (salida de `scan_imports`).
    shared_dir : Path | None
        Override de la raiz de `shared/` (para tests).

    Returns
    -------
    set[str]
        El cierre transitivo: `direct` mas todas las deps internas.

    Raises
    ------
    SharedResolverError
        Si se referencia un subpaquete inexistente.
    """
    root = shared_dir if shared_dir is not None else shared_root()
    available = available_subpackages(shared_dir=root)

    closure: set[str] = set()
    pending = set(direct)
    while pending:
        current = pending.pop()
        if current in closure:
            continue
        if current not in available:
            raise SharedResolverError(
                f'El lambda importa shared.{current} pero ese '
                f'subpaquete no existe en {root}.',
            )
        closure.add(current)
        _, internal = _read_manifest(current, shared_dir=root)
        pending |= set(internal) - closure
    return closure


def external_dependencies(
    closure: set[str],
    *,
    shared_dir: Path | None = None,
) -> list[str]:
    """Devuelve la union ordenada de deps externas de un cierre.

    Parameters
    ----------
    closure : set[str]
        Subpaquetes resueltos (salida de `resolve_closure`).
    shared_dir : Path | None
        Override de la raiz de `shared/` (para tests).

    Returns
    -------
    list[str]
        Specs de dependencias PyPI, deduplicadas y ordenadas.
    """
    root = shared_dir if shared_dir is not None else shared_root()
    deps: set[str] = set()
    for subpackage in closure:
        external, _ = _read_manifest(subpackage, shared_dir=root)
        deps |= set(external)
    return sorted(deps)


def resolve_lambda_shared(
    lambda_root: Path,
) -> tuple[set[str], list[str]]:
    """Resuelve que subpaquetes de `shared/` y deps necesita un lambda.

    Escanea `<lambda_root>/core/`, calcula el cierre transitivo y la
    union de deps externas. Es la API de alto nivel que usa el
    vendoring y el empaquetado.

    Parameters
    ----------
    lambda_root : Path
        Directorio raiz del lambda (donde vive `manifest.yaml`).

    Returns
    -------
    tuple[set[str], list[str]]
        `(closure, external_deps)` — los subpaquetes a vendorizar y las
        deps PyPI que aportan al zip.

    Raises
    ------
    SharedResolverError
        Si el lambda no tiene `core/` o la resolucion falla.
    """
    core_dir = lambda_root / 'core'
    if not core_dir.is_dir():
        raise SharedResolverError(
            f'El lambda {lambda_root} no tiene core/.',
        )
    direct = scan_imports(core_dir)
    closure = resolve_closure(direct)
    deps = external_dependencies(closure)
    return closure, deps
