"""Discovery automatico de manifests del monorepo portfolio.

Reemplaza los paths hardcoded de modulos como ``upgrade_deps`` y
``validate_versions``: en lugar de declarar a mano cada ``package.json`` o
``pyproject.toml``, este modulo enumera TODOS los workspaces conocidos
(``apps/*``, ``packages/*``, root, ``devtools/``, ``server/``) y devuelve
la lista de manifests existentes.

Single source of truth: si manana se agrega un workspace nuevo, basta con
extender ``PORTFOLIO_APPS`` o ``PORTFOLIO_PACKAGES`` en ``shared/paths.py``
y los scripts lo recogen automaticamente.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from shared.paths import APPS_DIR
from shared.paths import DEVTOOLS_DIR
from shared.paths import PACKAGES_DIR
from shared.paths import PORTFOLIO_APPS
from shared.paths import PORTFOLIO_PACKAGES
from shared.paths import PROJECT_ROOT
from shared.paths import SERVER_DIR


class Manifest(NamedTuple):
    """Un manifest descubierto, listo para parsear.

    Attributes:
        kind: ``'npm'`` para package.json o ``'pypi'`` para pyproject.toml.
        workspace: identificador legible (``'app:generic'``,
            ``'pkg:content'``, ``'root'``, ``'devtools'``, ``'server'``).
        path: ruta absoluta al manifest.
        relpath: ruta relativa a ``PROJECT_ROOT`` (POSIX style) para logs.
    """

    kind: str
    workspace: str
    path: Path
    relpath: str


def _make(kind: str, workspace: str, path: Path) -> Manifest | None:
    if not path.is_file():
        return None
    return Manifest(
        kind=kind,
        workspace=workspace,
        path=path,
        relpath=path.relative_to(PROJECT_ROOT).as_posix(),
    )


def discover_npm_manifests() -> list[Manifest]:
    """Devuelve TODOS los ``package.json`` del monorepo.

    Cubre:
        - ``package.json`` raiz (workspace orchestrator)
        - ``apps/<app>/package.json`` (6 sites Astro)
        - ``packages/<pkg>/package.json`` (5 workspaces compartidos)

    Solo retorna manifests que existen en disco; las apps/packages declaradas
    en ``PORTFOLIO_APPS`` / ``PORTFOLIO_PACKAGES`` que aun no tengan archivo
    se omiten silenciosamente.
    """
    out: list[Manifest] = []

    root_pkg = _make('npm', 'root', PROJECT_ROOT / 'package.json')
    if root_pkg is not None:
        out.append(root_pkg)

    for app in PORTFOLIO_APPS:
        manifest = _make('npm', f'app:{app}', APPS_DIR / app / 'package.json')
        if manifest is not None:
            out.append(manifest)

    for pkg in PORTFOLIO_PACKAGES:
        manifest = _make(
            'npm', f'pkg:{pkg}', PACKAGES_DIR / pkg / 'package.json'
        )
        if manifest is not None:
            out.append(manifest)

    return out


def discover_pypi_manifests() -> list[Manifest]:
    """Devuelve TODOS los ``pyproject.toml`` del monorepo.

    Cubre:
        - ``devtools/pyproject.toml`` (Python 3.14 CLI orchestrator)
        - ``server/pyproject.toml`` (stub, si existe — el portfolio no tiene
          backend, pero el manifest puede existir para futuros usos)
    """
    out: list[Manifest] = []

    devtools_pyproject = _make(
        'pypi', 'devtools', DEVTOOLS_DIR / 'pyproject.toml'
    )
    if devtools_pyproject is not None:
        out.append(devtools_pyproject)

    server_pyproject = _make('pypi', 'server', SERVER_DIR / 'pyproject.toml')
    if server_pyproject is not None:
        out.append(server_pyproject)

    return out


def discover_all() -> list[Manifest]:
    """Devuelve npm + pypi manifests, en ese orden."""
    return [*discover_npm_manifests(), *discover_pypi_manifests()]
