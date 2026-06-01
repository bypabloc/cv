"""@module devtools.serverless.submodule_import_validator — no-submodule check.

Prohibe importar un SUBMODULO de `shared` via su paquete padre con
`from`. El contrato del backend (`.claude/rules/lambda-shared-imports.md`)
exige importar el simbolo concreto (clase/funcion) desde el modulo que lo
define, NO el submodulo-objeto via el barrel del paquete.

    # PROHIBIDO (importa el submodulo `webauthn` via el paquete `shared.auth`)
    from shared.auth import webauthn

    # CORRECTO (importa el simbolo concreto del modulo que lo define)
    from shared.auth.webauthn import WebauthnCloneError

    # CORRECTO para acceso al modulo (monkeypatch / side-effect): plain import
    import shared.auth.webauthn as webauthn

Solo se flaggean los `ImportFrom` (`from shared.X import <submodulo>`). Los
`import shared.X.Y` (plain `Import`) quedan permitidos: dan el objeto-modulo
para monkeypatch en tests o imports con efecto secundario (registry de
modelos para Alembic).

Escanea TODO `serverless/lambda/**/*.py` (services + shared, incluyendo
tests), excepto la copia vendorizada `*/core/shared/`, los `build/` y los
`.venv/`. Forma parte de `serverless lint-deps`.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


_SKIP_DIR_PARTS = frozenset({'__pycache__', '.venv', 'build', 'node_modules'})


@dataclass(frozen=True)
class SubmoduleImport:
    """Reporta un `from shared.X import <submodulo>` prohibido."""

    path: Path
    lineno: int
    module: str
    name: str


def _module_to_dir(module: str, shared_root: Path) -> Path:
    """Mapea un dotted module bajo `shared` a su directorio en el filesystem.

    'shared'           -> <shared_root>
    'shared.auth'      -> <shared_root>/auth
    'shared.db.models' -> <shared_root>/db/models
    """
    rest = module[len('shared'):].lstrip('.')
    directory = shared_root
    if rest:
        for part in rest.split('.'):
            directory = directory / part
    return directory


def _is_submodule(module: str, name: str, shared_root: Path) -> bool:
    """True si `<module>.<name>` es un modulo/subpaquete en disco."""
    directory = _module_to_dir(module, shared_root)
    return (directory / f'{name}.py').is_file() or (
        directory / name / '__init__.py'
    ).is_file()


def _iter_submodule_imports(
    tree: ast.Module, shared_root: Path
) -> Iterator[tuple[int, str, str]]:
    """Itera (lineno, module, name) de cada `from shared.X import <submodulo>`."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.level:
            continue
        module = node.module
        if module is None:
            continue
        if module != 'shared' and not module.startswith('shared.'):
            continue
        for alias in node.names:
            if _is_submodule(module, alias.name, shared_root):
                yield node.lineno, module, alias.name


def scan_file(path: Path, shared_root: Path) -> list[SubmoduleImport]:
    """Escanea un .py; devuelve los `from shared.X import <submodulo>`."""
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except (SyntaxError, OSError, UnicodeDecodeError):
        return []
    return [
        SubmoduleImport(path, lineno, module, name)
        for lineno, module, name in _iter_submodule_imports(tree, shared_root)
    ]


def _should_skip(py: Path, scan_root: Path) -> bool:
    """Salta __pycache__/.venv/build/node_modules y la copia vendorizada."""
    rel_parts = py.relative_to(scan_root).parts
    if any(part in _SKIP_DIR_PARTS for part in rel_parts):
        return True
    # Copia vendorizada de shared en cada lambda: services/<x>/core/shared/**
    return 'core' in rel_parts and 'shared' in rel_parts[
        rel_parts.index('core') + 1 : rel_parts.index('core') + 2
    ]


def scan_tree(scan_root: Path, shared_root: Path) -> list[SubmoduleImport]:
    """Escanea recursivamente `scan_root/**/*.py`."""
    violations: list[SubmoduleImport] = []
    for py in sorted(scan_root.rglob('*.py')):
        if _should_skip(py, scan_root):
            continue
        violations.extend(scan_file(py, shared_root))
    return violations


def format_report(
    violations: list[SubmoduleImport], scan_root: Path
) -> str:
    """Formatea las violaciones para impresion CLI."""
    if not violations:
        return 'OK  serverless: cero imports de submodulo via barrel shared.'
    lines = [
        f'FAIL  serverless: {len(violations)} import(s) de submodulo via '
        f'barrel shared (importa el simbolo concreto):',
    ]
    for v in violations:
        rel = v.path.relative_to(scan_root)
        lines.append(
            f'  - {rel}:{v.lineno} -> from {v.module} import {v.name}'
            f'\n    usa `from {v.module}.{v.name} import <simbolo>` '
            f'o `import {v.module}.{v.name} as {v.name}` (modulo). '
            f'Ver .claude/rules/lambda-shared-imports.md.',
        )
    return '\n'.join(lines)
