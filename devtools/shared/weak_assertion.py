"""Weak assertion detector for test files.

Identifica asserts vagos via AST en archivos de test Python:

- ``assert x > 0`` / ``assert x < N`` / ``assert x >= 0`` / ``assert x <= N``
- ``assert result is not None`` / ``assert x is None``
- ``assert isinstance(x, T)`` (cuando es la única forma de verificar)
- ``assert len(x) > 0`` / ``assert len(x) >= 1``
- ``assert x``  (truthy check sin valor concreto)

Estos patrones suelen indicar tests que pasan por casualidad (no demuestran
el comportamiento esperado). Política completa:
``.claude/rules/ai-testing-independence.md``.

Bypass:
- Por linea: agregar ``# noqa: WEAK-ASSERT`` con razón en comentario.
- Por archivo: agregar ``# weak-assert: skip-file`` en una linea.
- Por step: ``SKIP_STEPS="weak_assertion" git commit ...``

Esta lógica se invoca desde:
- El step ``weak_assertion`` del orquestador de hooks (``.git-hooks/_common.py``).
- El script ``devtools/run.py weak_assertion`` (CLI manual).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WeakAssertFinding:
    """Resultado: una weak assertion detectada en un archivo."""

    file: Path
    line: int
    code_excerpt: str
    pattern: str
    suggestion: str


# ── Detectores AST ───────────────────────────────────────────────────────


def _is_compare_with_zero_or_int(node: ast.Compare) -> tuple[bool, str]:
    """Detecta ``x > 0``, ``x >= 0``, ``x < N``, ``x <= N``."""
    if not node.ops or len(node.ops) != 1:
        return False, ''
    op = node.ops[0]
    if not isinstance(op, ast.Gt | ast.GtE | ast.Lt | ast.LtE):
        return False, ''
    if not node.comparators or len(node.comparators) != 1:
        return False, ''
    comp = node.comparators[0]
    # Solo flagear contra Constant numerico (no contra otra expresión)
    if not isinstance(comp, ast.Constant) or not isinstance(
        comp.value, int | float
    ):
        return False, ''
    op_str = {
        ast.Gt: '>',
        ast.GtE: '>=',
        ast.Lt: '<',
        ast.LtE: '<=',
    }[type(op)]
    return True, f'comparación {op_str} {comp.value}'


def _is_isnone(node: ast.Compare) -> tuple[bool, str]:
    """Detecta ``x is not None`` / ``x is None``."""
    if not node.ops or len(node.ops) != 1:
        return False, ''
    op = node.ops[0]
    if not isinstance(op, ast.Is | ast.IsNot):
        return False, ''
    if not node.comparators or len(node.comparators) != 1:
        return False, ''
    comp = node.comparators[0]
    if not (isinstance(comp, ast.Constant) and comp.value is None):
        return False, ''
    return True, 'is not None' if isinstance(op, ast.IsNot) else 'is None'


def _is_isinstance_call(node: ast.Call) -> tuple[bool, str]:
    """Detecta ``isinstance(x, T)`` como assert standalone."""
    if not isinstance(node.func, ast.Name) or node.func.id != 'isinstance':
        return False, ''
    return True, 'isinstance(...)'


def _is_len_compare(node: ast.Compare) -> tuple[bool, str]:
    """Detecta ``len(x) > 0`` / ``len(x) >= 1`` / ``len(x) >= 0``."""
    if not isinstance(node.left, ast.Call):
        return False, ''
    func = node.left.func
    if not isinstance(func, ast.Name) or func.id != 'len':
        return False, ''
    if not node.ops or len(node.ops) != 1:
        return False, ''
    op = node.ops[0]
    if not isinstance(op, ast.Gt | ast.GtE):
        return False, ''
    return True, 'len(...) > 0  o  len(...) >= 1'


def _classify_assert(test: ast.expr) -> tuple[str, str] | None:
    """Clasifica el target de un ``assert``. Retorna (pattern, suggestion).

    Retorna None si el assert no es weak.
    """
    # 1) Truthy check standalone: assert x  (Name o Attribute, sin operación)
    if isinstance(test, ast.Name | ast.Attribute):
        return (
            'truthy check sin valor concreto',
            'usar comparación exacta: assert x == <valor_esperado>',
        )

    # 2) Comparaciones vagas
    if isinstance(test, ast.Compare):
        is_weak, label = _is_compare_with_zero_or_int(test)
        if is_weak:
            return (
                f'comparación vaga ({label})',
                'usar igualdad exacta: assert x == <valor_esperado>',
            )
        is_weak, label = _is_isnone(test)
        if is_weak:
            return (
                f'check de None ({label})',
                'usar igualdad exacta: assert x == <valor_esperado>',
            )
        is_weak, label = _is_len_compare(test)
        if is_weak:
            return (
                f'len comparado ({label})',
                'usar contenido exacto: assert items == [item_a, item_b]',
            )

    # 3) isinstance standalone
    if isinstance(test, ast.Call):
        is_weak, label = _is_isinstance_call(test)
        if is_weak:
            return (
                f'verificación de tipo ({label})',
                'usar igualdad de valor + relegar tipo a typecheck estático',
            )

    return None


# ── Bypass markers ───────────────────────────────────────────────────────


def _has_inline_skip(line: str) -> bool:
    """¿La linea tiene ``# noqa: WEAK-ASSERT``?"""
    return '# noqa: WEAK-ASSERT' in line or '# noqa:WEAK-ASSERT' in line


def _has_file_skip(source: str) -> bool:
    """¿El archivo tiene ``# weak-assert: skip-file``?"""
    return any(
        '# weak-assert: skip-file' in line for line in source.splitlines()
    )


# ── API pública ──────────────────────────────────────────────────────────


def is_test_file(path: Path) -> bool:
    """¿Es archivo Python dentro de algun directorio ``tests/``?"""
    if path.suffix != '.py':
        return False
    return 'tests' in path.parts


def scan_file(file_path: Path) -> list[WeakAssertFinding]:
    """Escanea un archivo Python y retorna findings de weak assertions."""
    try:
        source = file_path.read_text(encoding='utf-8')
    except OSError, UnicodeDecodeError:
        return []

    if _has_file_skip(source):
        return []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        # Si no parsea, lo dejamos pasar — Ruff capturara el error.
        return []

    source_lines = source.splitlines()
    findings: list[WeakAssertFinding] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue

        # Skip inline via noqa
        line_idx = node.lineno - 1
        in_range = 0 <= line_idx < len(source_lines)
        if in_range and _has_inline_skip(source_lines[line_idx]):
            continue

        classification = _classify_assert(node.test)
        if classification is None:
            continue
        pattern, suggestion = classification

        excerpt = (
            source_lines[line_idx].strip()
            if 0 <= line_idx < len(source_lines)
            else '<unavailable>'
        )

        findings.append(
            WeakAssertFinding(
                file=file_path,
                line=node.lineno,
                code_excerpt=excerpt,
                pattern=pattern,
                suggestion=suggestion,
            )
        )

    return findings


def scan_files(
    files: list[str], *, project_root: Path
) -> list[WeakAssertFinding]:
    """Escanea una lista de paths (relativos o absolutos) y retorna findings.

    Solo se procesan los que están bajo un directorio ``tests/`` y existen en
    disco. Paths sin extensión ``.py`` se ignoran.
    """
    findings: list[WeakAssertFinding] = []
    for f in files:
        path = Path(f)
        if not path.is_absolute():
            path = project_root / path
        if not is_test_file(path):
            continue
        if not path.exists():
            continue
        findings.extend(scan_file(path))
    return findings


def format_findings(findings: list[WeakAssertFinding]) -> str:
    """Formatea findings en multilinea legible para CLI/hooks."""
    n = len(findings)
    plural = 's' if n != 1 else ''
    lines = [f'\n[weak_assertion] {n} weak assert{plural} detectado{plural}:\n']
    lines.extend(
        f'  {f.file}:{f.line}\n'
        f'      |  {f.code_excerpt}\n'
        f'      |  patron: {f.pattern}\n'
        f'      |  fix:    {f.suggestion}'
        for f in findings
    )
    lines.append(
        '\nBypass:\n'
        '  - inline: agregar  # noqa: WEAK-ASSERT  con razón en comentario\n'
        '  - archivo: agregar  # weak-assert: skip-file  en una linea\n'
        '  - emergencia: SKIP_STEPS="weak_assertion" git commit ...\n'
        '\nPolitica: .claude/rules/ai-testing-independence.md',
    )
    return '\n'.join(lines)
