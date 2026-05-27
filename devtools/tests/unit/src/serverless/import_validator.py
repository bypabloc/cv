"""Unit tests for serverless.import_validator - scanner de imports prohibidos.

Path mirroring: devtools/serverless/import_validator.py -> this file.

Verifica que el scanner detecta imports directos a paquetes externos en
`services/<X>/core/**/*.py` (que deberian importarse desde `shared.*`) y
que ignora correctamente:
- imports de `shared.*` (el patron correcto).
- imports relativos (`from . import x`).
- archivos con SyntaxError (otro check los reporta).
- `core/shared/` (copia vendorizada).
- `tests/` del lambda (queda fuera del scope).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from serverless.import_validator import ForbiddenImport
from serverless.import_validator import scan_file
from serverless.import_validator import scan_lambda_core


pytestmark = pytest.mark.unit


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    return path


def test_scan_file_detects_pydantic_import(tmp_path: Path) -> None:
    """
    Given un .py con `from pydantic import BaseModel`,
    When scan_file lo procesa,
    Then la lista contiene UN ForbiddenImport(package='pydantic', lineno=1).
    """
    # Arrange
    p = _write(tmp_path / 'x.py', 'from pydantic import BaseModel\n')

    # Act
    result = scan_file(p)

    # Assert
    assert len(result) == 1
    assert result[0].package == 'pydantic'
    assert result[0].lineno == 1


def test_scan_file_ignores_shared_imports(tmp_path: Path) -> None:
    """
    Given un .py con `from shared.core import BaseModel`,
    When scan_file lo procesa,
    Then la lista es vacia (shared.* es el patron correcto).
    """
    # Arrange
    p = _write(tmp_path / 'x.py', 'from shared.core import BaseModel\n')

    # Act
    result = scan_file(p)

    # Assert
    assert result == []


def test_scan_file_ignores_stdlib(tmp_path: Path) -> None:
    """
    Given un .py con imports de stdlib (os, json, ast),
    When scan_file lo procesa,
    Then la lista es vacia.
    """
    # Arrange
    p = _write(
        tmp_path / 'x.py',
        'import os\nimport json\nfrom pathlib import Path\n',
    )

    # Act
    result = scan_file(p)

    # Assert
    assert result == []


def test_scan_file_detects_boto3_dynamodb_types(tmp_path: Path) -> None:
    """
    Given un .py con `from boto3.dynamodb.types import TypeDeserializer`,
    When scan_file lo procesa,
    Then detecta el root 'boto3' como paquete prohibido.
    """
    # Arrange
    p = _write(
        tmp_path / 'x.py',
        'from boto3.dynamodb.types import TypeDeserializer\n',
    )

    # Act
    result = scan_file(p)

    # Assert
    assert len(result) == 1
    assert result[0].package == 'boto3'


def test_scan_file_detects_aws_lambda_powertools(tmp_path: Path) -> None:
    """
    Given un .py con `from aws_lambda_powertools.metrics import MetricUnit`,
    When scan_file lo procesa,
    Then detecta 'aws_lambda_powertools' como paquete prohibido.
    """
    # Arrange
    p = _write(
        tmp_path / 'x.py',
        'from aws_lambda_powertools.metrics import MetricUnit\n',
    )

    # Act
    result = scan_file(p)

    # Assert
    assert len(result) == 1
    assert result[0].package == 'aws_lambda_powertools'


def test_scan_file_handles_syntax_error_gracefully(tmp_path: Path) -> None:
    """
    Given un .py con SyntaxError,
    When scan_file lo procesa,
    Then devuelve lista vacia (no lanza la excepcion; otro check lo reporta).
    """
    # Arrange
    p = _write(tmp_path / 'x.py', 'def broken(\n')  # parentesis sin cerrar

    # Act
    result = scan_file(p)

    # Assert
    assert result == []


def test_scan_file_ignores_relative_imports(tmp_path: Path) -> None:
    """
    Given un .py con `from . import x`,
    When scan_file lo procesa,
    Then la lista es vacia (los relativos no aplican al contrato).
    """
    # Arrange
    p = _write(tmp_path / 'x.py', 'from . import sibling\n')

    # Act
    result = scan_file(p)

    # Assert
    assert result == []


def test_scan_lambda_core_walks_recursively(tmp_path: Path) -> None:
    """
    Given una raiz de lambda con `core/services/x.py` con import prohibido
         y `core/models/y.py` sin imports prohibidos,
    When scan_lambda_core lo procesa,
    Then devuelve solo la violacion de x.py.
    """
    # Arrange
    lambda_root = tmp_path / 'mylambda'
    _write(
        lambda_root / 'core' / 'services' / 'x.py',
        'from sqlalchemy import select\n',
    )
    _write(
        lambda_root / 'core' / 'models' / 'y.py',
        'from shared.core import BaseModel\n',
    )

    # Act
    result = scan_lambda_core(lambda_root)

    # Assert
    assert len(result) == 1
    assert result[0].package == 'sqlalchemy'
    assert result[0].path.name == 'x.py'


def test_scan_lambda_core_skips_tests_dir(tmp_path: Path) -> None:
    """
    Given un lambda con `tests/unit/x.py` importando pydantic,
    When scan_lambda_core lo procesa,
    Then la lista es vacia (tests/ esta fuera del scope del contrato).
    """
    # Arrange
    lambda_root = tmp_path / 'mylambda'
    _write(
        lambda_root / 'tests' / 'unit' / 'x.py',
        'from pydantic import BaseModel\n',
    )
    # Tambien creamos core/ vacio para que el directorio exista.
    (lambda_root / 'core').mkdir(parents=True, exist_ok=True)

    # Act
    result = scan_lambda_core(lambda_root)

    # Assert
    assert result == []


def test_scan_lambda_core_skips_vendored_shared(tmp_path: Path) -> None:
    """
    Given un lambda con `core/shared/aws/ses.py` que importa boto3 (es la
         copia vendorizada de shared/),
    When scan_lambda_core lo procesa,
    Then la lista es vacia (core/shared/ es la copia, no codigo del service).
    """
    # Arrange
    lambda_root = tmp_path / 'mylambda'
    _write(
        lambda_root / 'core' / 'shared' / 'aws' / 'ses.py',
        'import boto3\n',
    )
    _write(
        lambda_root / 'core' / 'services' / 'mine.py',
        'from shared.aws import send_email\n',
    )

    # Act
    result = scan_lambda_core(lambda_root)

    # Assert
    assert result == []


def test_scan_lambda_core_returns_empty_when_no_core(tmp_path: Path) -> None:
    """
    Given una raiz que no tiene `core/`,
    When scan_lambda_core lo procesa,
    Then devuelve lista vacia (no lanza).
    """
    # Arrange + Act
    result = scan_lambda_core(tmp_path)

    # Assert
    assert result == []


def test_forbidden_import_is_frozen_dataclass() -> None:
    """
    Given una instancia de ForbiddenImport,
    When intento modificar un campo,
    Then lanza FrozenInstanceError (es @dataclass(frozen=True)).
    """
    # Arrange
    from dataclasses import FrozenInstanceError

    v = ForbiddenImport(
        path=Path('x.py'), lineno=1, statement='import x', package='x'
    )

    # Act + Assert
    with pytest.raises(FrozenInstanceError):
        v.lineno = 99  # type: ignore[misc]
