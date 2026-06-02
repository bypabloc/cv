"""Unit tests for serverless.submodule_import_validator.

Path mirroring: devtools/serverless/submodule_import_validator.py -> este file.

Verifica que el scanner detecta `from shared.X import <submodulo>` (importar
el submodulo-objeto via el barrel) y que NO flaggea:
- `from shared.X.Y import <simbolo>` (el patron correcto).
- `import shared.X.Y as Y` (plain Import: acceso al modulo, monkeypatch).
- simbolos que no son submodulos.
- la copia vendorizada `core/shared/`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from serverless.submodule_import_validator import scan_file
from serverless.submodule_import_validator import scan_tree


pytestmark = pytest.mark.unit


def _fake_shared(root: Path) -> Path:
    """Crea un arbol `shared/` minimo para resolver submodulos."""
    shared = root / 'shared'
    for rel in (
        'auth/webauthn.py',
        'auth/admin.py',
        'aws/ssm.py',
        'db/models/auth/__init__.py',
    ):
        p = shared / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('', encoding='utf-8')
    return shared


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    return path


def test_scan_file_flags_submodule_via_barrel(tmp_path: Path) -> None:
    """
    Given `from shared.auth import webauthn` y existe shared/auth/webauthn.py,
    When scan_file lo procesa,
    Then reporta UNA violacion (module='shared.auth', name='webauthn').
    """
    # Arrange
    shared = _fake_shared(tmp_path)
    p = _write(tmp_path / 'x.py', 'from shared.auth import webauthn\n')

    # Act
    result = scan_file(p, shared)

    # Assert
    assert len(result) == 1
    assert result[0].module == 'shared.auth'
    assert result[0].name == 'webauthn'
    assert result[0].lineno == 1


def test_scan_file_flags_subpackage_via_barrel(tmp_path: Path) -> None:
    """
    Given `from shared.db.models import auth` con shared/db/models/auth/ pkg,
    When scan_file lo procesa,
    Then reporta UNA violacion (name='auth').
    """
    # Arrange
    shared = _fake_shared(tmp_path)
    p = _write(tmp_path / 'x.py', 'from shared.db.models import auth\n')

    # Act
    result = scan_file(p, shared)

    # Assert
    assert len(result) == 1
    assert result[0].name == 'auth'


def test_scan_file_ignores_concrete_symbol_import(tmp_path: Path) -> None:
    """
    Given `from shared.auth.webauthn import WebauthnCloneError`,
    When scan_file lo procesa,
    Then la lista es vacia (WebauthnCloneError no es un submodulo).
    """
    # Arrange
    shared = _fake_shared(tmp_path)
    p = _write(
        tmp_path / 'x.py',
        'from shared.auth.webauthn import WebauthnCloneError\n',
    )

    # Act
    result = scan_file(p, shared)

    # Assert
    assert result == []


def test_scan_file_ignores_plain_import_as(tmp_path: Path) -> None:
    """
    Given `import shared.auth.webauthn as wa` (plain Import),
    When scan_file lo procesa,
    Then la lista es vacia (Import, no ImportFrom: permitido).
    """
    # Arrange
    shared = _fake_shared(tmp_path)
    p = _write(tmp_path / 'x.py', 'import shared.auth.webauthn as wa\n')

    # Act
    result = scan_file(p, shared)

    # Assert
    assert result == []


def test_scan_file_ignores_non_submodule_name(tmp_path: Path) -> None:
    """
    Given `from shared.aws.ssm import get_secret` (get_secret no es modulo),
    When scan_file lo procesa,
    Then la lista es vacia.
    """
    # Arrange
    shared = _fake_shared(tmp_path)
    p = _write(tmp_path / 'x.py', 'from shared.aws.ssm import get_secret\n')

    # Act
    result = scan_file(p, shared)

    # Assert
    assert result == []


def test_scan_tree_skips_vendored_core_shared(tmp_path: Path) -> None:
    """
    Given una violacion dentro de services/x/core/shared/ (copia vendorizada),
    When scan_tree procesa el arbol,
    Then NO se reporta (la copia vendorizada queda fuera de scope).
    """
    # Arrange
    shared = _fake_shared(tmp_path)
    _write(
        tmp_path / 'services/x/core/shared/y.py',
        'from shared.auth import webauthn\n',
    )

    # Act
    result = scan_tree(tmp_path, shared)

    # Assert
    assert result == []
