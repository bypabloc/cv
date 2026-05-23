"""@module devtools.serverless.import_validator — check de imports prohibidos.

Escanea los archivos `services/<X>/core/**/*.py` y detecta imports
directos a paquetes externos que tienen un portador shared en el backend
(`pydantic`, `sqlalchemy`, `alembic`, `psycopg`, `boto3`, `botocore`,
`aws_lambda_powertools`, `pydantic_settings`). Los services deben
importarlos desde `shared.*` (ver `.claude/rules/lambda-shared-imports.md`).

Forma parte del comando `serverless lint-deps`: junto con el check de
dedup D-3 (`dep_validator`) garantiza que el contrato shared-only se
respeta tanto en `pyproject.toml` como en el codigo del lambda.

`tests/` del service queda fuera del scope: los mocks de pydantic/boto3
en tests son aceptables (no se vendorizan al zip de deploy).
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


# Paquetes raiz que NO deben importarse directamente en services/*/core/.
# El service debe importarlos desde shared.* (que actua como portador).
_FORBIDDEN_ROOTS = frozenset(
    {
        'pydantic',
        'pydantic_settings',
        'sqlalchemy',
        'alembic',
        'psycopg',
        'boto3',
        'botocore',
        'aws_lambda_powertools',
    }
)


@dataclass(frozen=True)
class ForbiddenImport:
    """Reporta una violacion de import directo en `core/`."""

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
            # `from . import x` -> module=None / level > 0; ignorar (relativo).
            if node.module is None or node.level > 0:
                continue
            root = _root_of(node.module)
            yield node.lineno, f'from {node.module} import ...', root


def scan_file(path: Path) -> list[ForbiddenImport]:
    """Escanea un .py y devuelve los imports prohibidos encontrados.

    Si el archivo tiene SyntaxError, devuelve lista vacia — otro check
    (typecheck / ruff) reportara el problema. No es responsabilidad del
    import_validator detectar sintaxis invalida.
    """
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except (SyntaxError, OSError, UnicodeDecodeError):
        return []
    return [
        ForbiddenImport(path, lineno, statement, root)
        for lineno, statement, root in _iter_imports(tree)
        if root in _FORBIDDEN_ROOTS
    ]


def scan_lambda_core(lambda_root: Path) -> list[ForbiddenImport]:
    """Escanea recursivamente `<lambda_root>/core/**/*.py`.

    `tests/` del lambda NO se escanea (queda fuera del contrato shared-only).
    `core/shared/` tampoco — es la copia vendorizada, no codigo del service.
    """
    core = lambda_root / 'core'
    if not core.is_dir():
        return []
    violations: list[ForbiddenImport] = []
    for py in sorted(core.rglob('*.py')):
        # Excluir la copia vendorizada de shared/ que devtools deja en
        # core/shared/ al correr tests o al armar el build.
        if 'shared' in py.relative_to(core).parts[:1]:
            continue
        violations.extend(scan_file(py))
    return violations


def format_import_report(
    violations: list[ForbiddenImport], lambda_root: Path
) -> str:
    """Formatea las violaciones para impresion CLI."""
    if not violations:
        return ''
    lines = [
        f'FAIL  {lambda_root.name}: {len(violations)} import(s) prohibido(s) '
        f'directo(s) en core/:',
    ]
    for v in violations:
        rel = v.path.relative_to(lambda_root)
        lines.append(
            f'  - {rel}:{v.lineno} -> {v.statement}'
            f'\n    paquete prohibido: {v.package!r}. '
            f'Importa desde shared.* (ver .claude/rules/lambda-shared-imports.md).',
        )
    return '\n'.join(lines)
