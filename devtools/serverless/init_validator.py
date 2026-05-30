"""Check de conformance: los `__init__.py` de `serverless/lambda/` deben
estar VACIOS (sin re-exports / barrels).

Regla (`.claude/rules/lambda-shared-imports.md`): ningun `__init__.py` bajo
`serverless/lambda/{shared,services}` re-exporta simbolos. Los consumidores
importan SIEMPRE del modulo concreto (`from shared.db.models.auth.user
import AuthUser`), nunca del barrel del paquete. Esto vale tanto entre
`shared` como en los `services` (igual que el contrato shared-only de
imports concretos por modulo).

Un `__init__.py` puede contener docstring, comentarios y `from __future__
import annotations`. Cualquier otro import a nivel modulo, o una asignacion
a `__all__`, es una violacion (es un barrel).

`tests/` queda EXENTO (los `_fixtures/__init__.py` de integration pueden
re-exportar builders de test sin impacto en el runtime del lambda).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path


# Directorios que NO se escanean (artefactos / entornos).
_SKIP_DIRS = frozenset({
    '.venv', 'build', 'site-packages', '__pycache__', '.pytest_cache',
    'node_modules', 'dist', '.mypy_cache', '.ruff_cache', '.egg-info',
})


@dataclass
class InitViolation:
    """Un `__init__.py` con imports/re-exports a nivel modulo."""

    path: Path
    statements: list[str] = field(default_factory=list)


def _offending_statements(source: str) -> list[str]:
    """Devuelve las sentencias a nivel modulo que convierten el init en barrel.

    Ignora docstring, comentarios y `from __future__`. Reporta Import,
    ImportFrom (no-future) y asignaciones a `__all__`.
    """
    tree = ast.parse(source)
    out: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            if node.module == '__future__':
                continue
            names = ', '.join(a.name for a in node.names)
            dots = '.' * node.level
            out.append(f'from {dots}{node.module or ""} import {names}')
        elif isinstance(node, ast.Import):
            out.append('import ' + ', '.join(a.name for a in node.names))
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == '__all__':
                    out.append('__all__ = [...]')
    return out


def scan_empty_inits(scan_root: Path) -> list[InitViolation]:
    """Escanea recursivamente `scan_root` y devuelve los `__init__.py` barrel.

    Salta artefactos (`.venv`, `build`, ...) y la carpeta `tests/`.
    """
    violations: list[InitViolation] = []
    for init in sorted(scan_root.rglob('__init__.py')):
        parts = set(init.parts)
        if _SKIP_DIRS & parts or any(p.endswith('.egg-info') for p in init.parts):
            continue
        if 'tests' in init.relative_to(scan_root).parts:
            continue
        stmts = _offending_statements(init.read_text(encoding='utf-8'))
        if stmts:
            violations.append(InitViolation(path=init, statements=stmts))
    return violations


def format_report(violations: list[InitViolation], scan_root: Path) -> str:
    """Reporte legible del check de inits vacios."""
    if not violations:
        return 'OK  serverless: todos los __init__.py vacios (sin barrels).'
    lines = [
        f'FAIL serverless: {len(violations)} __init__.py con re-exports '
        '(barrels prohibidos):',
    ]
    for v in violations:
        rel = v.path.relative_to(scan_root)
        lines.append(f'  {rel}')
        for s in v.statements:
            lines.append(f'      {s}')
    lines.append(
        '  -> Vacia el __init__.py (docstring-only). Los consumidores '
        'importan del modulo concreto.',
    )
    return '\n'.join(lines)
