"""Unit tests for serverless.init_validator.

Path mirroring: devtools/serverless/init_validator.py -> este file.

Verifica que el scanner detecta `__init__.py` barrel (con imports o
`__all__`) y que NO flaggea:
- inits docstring-only (con o sin `from __future__`).
- inits bajo `tests/` (exentos).
- inits bajo `.venv` / `build` (artefactos).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from serverless.init_validator import scan_empty_inits


pytestmark = pytest.mark.unit


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def test_empty_init_docstring_only_is_clean(tmp_path: Path) -> None:
    """
    Given un __init__.py con solo docstring (+ from __future__),
    When scan_empty_inits,
    Then no lo reporta (no es barrel).
    """
    _write(
        tmp_path / 'shared' / 'db' / '__init__.py',
        '"""Subpaquete db.\n\nEjemplo: from shared.db.sa import select\n"""\n'
        'from __future__ import annotations\n',
    )

    result = scan_empty_inits(tmp_path)

    assert result == []


def test_init_with_from_import_is_violation(tmp_path: Path) -> None:
    """
    Given un __init__.py con `from .user import AuthUser`,
    When scan_empty_inits,
    Then lo reporta con esa sentencia.
    """
    _write(
        tmp_path / 'shared' / 'db' / 'models' / 'auth' / '__init__.py',
        '"""auth."""\nfrom .user import AuthUser\n',
    )

    result = scan_empty_inits(tmp_path)

    assert len(result) == 1
    assert (
        result[0].path
        == tmp_path / 'shared' / 'db' / 'models' / 'auth' / '__init__.py'
    )
    assert result[0].statements == ['from .user import AuthUser']


def test_init_with_absolute_import_is_violation(tmp_path: Path) -> None:
    """
    Given un __init__.py con `import shared.db.models.cv`,
    When scan_empty_inits,
    Then lo reporta.
    """
    _write(
        tmp_path / 'shared' / 'x' / '__init__.py',
        '"""x."""\nimport shared.db.models.cv\n',
    )

    result = scan_empty_inits(tmp_path)

    assert result[0].statements == ['import shared.db.models.cv']


def test_init_with_dunder_all_is_violation(tmp_path: Path) -> None:
    """
    Given un __init__.py con `__all__ = [...]`,
    When scan_empty_inits,
    Then lo reporta.
    """
    _write(
        tmp_path / 'services' / 'auth' / 'core' / '__init__.py',
        '"""core."""\n__all__ = [\'x\']\n',
    )

    result = scan_empty_inits(tmp_path)

    assert result[0].statements == ['__all__ = [...]']


def test_tests_dir_init_is_exempt(tmp_path: Path) -> None:
    """
    Given un __init__.py barrel bajo tests/,
    When scan_empty_inits,
    Then NO lo reporta (tests exentos).
    """
    _write(
        tmp_path
        / 'services'
        / 'auth'
        / 'tests'
        / 'integration'
        / '_fixtures'
        / '__init__.py',
        '"""fixtures."""\nfrom .builders import make_user\n',
    )

    result = scan_empty_inits(tmp_path)

    assert result == []


def test_venv_and_build_inits_are_skipped(tmp_path: Path) -> None:
    """
    Given inits barrel bajo .venv y build,
    When scan_empty_inits,
    Then NO los reporta (artefactos).
    """
    _write(
        tmp_path / 'shared' / '.venv' / 'lib' / 'pkg' / '__init__.py',
        'from .a import b\n',
    )
    _write(
        tmp_path / 'services' / 'auth' / 'build' / 'core' / '__init__.py',
        'from .a import b\n',
    )

    result = scan_empty_inits(tmp_path)

    assert result == []
