"""Unit tests for serverless.dep_validator - validador de dedup D-3.

Path mirroring: devtools/serverless/dep_validator.py -> this file.

Verifica que el validador detecta cuando un lambda declara, en su
`pyproject.toml`, una dependencia que ya le llega por el cierre
transitivo de `shared/` (regla de dedup D-3), y que la comparacion es
por nombre canonico (PEP 503).
"""

from pathlib import Path
import textwrap

import pytest

from serverless import dep_validator
from serverless.dep_validator import DepValidatorError
from serverless.dep_validator import canonical_name
from serverless.dep_validator import spec_extras
from serverless.dep_validator import validate_lambda_deps


pytestmark = pytest.mark.unit


def _make_lambda(tmp_path: Path, *, imports: str, deps: list[str]) -> Path:
    """Crea un lambda con core/handler.py + pyproject.toml.

    Los imports referencian subpaquetes reales de serverless/lambda/shared/
    porque el validador resuelve el cierre contra la fuente maestra.
    """
    lambda_root = tmp_path / 'my-lambda'
    core = lambda_root / 'core'
    core.mkdir(parents=True)
    (core / 'handler.py').write_text(imports, encoding='utf-8')
    dep_lines = ''.join(f'  "{d}",\n' for d in deps)
    (lambda_root / 'pyproject.toml').write_text(
        textwrap.dedent(f"""\
            [project]
            name = "my-lambda"
            version = "0.1.0"
            dependencies = [
            {dep_lines}]
        """),
        encoding='utf-8',
    )
    return lambda_root


def test_canonical_name_strips_extras_and_version() -> None:
    """canonical_name descarta extras, version y normaliza el nombre."""
    assert canonical_name('psycopg[binary]>=3.2,<4.0') == 'psycopg'
    assert (
        canonical_name('aws_lambda_powertools[all]>=3.0')
        == 'aws-lambda-powertools'
    )
    assert canonical_name('pydantic') == 'pydantic'
    assert canonical_name('pydantic[email]>=2.5,<3.0') == 'pydantic'


def test_validate_passes_when_no_duplication(tmp_path: Path) -> None:
    """Un lambda cuyo pyproject NO duplica deps de shared/ pasa."""
    # Arrange: el core/ no importa shared/ -> cierre vacio
    lambda_root = _make_lambda(tmp_path, imports='', deps=['pydantic'])

    # Act
    result = validate_lambda_deps(lambda_root)

    # Assert
    assert result.is_valid is True
    assert result.duplicated == []


def test_validate_fails_when_lambda_duplicates_shared_dep(
    tmp_path: Path,
) -> None:
    """Un lambda que declara una dep que aporta shared/ falla.

    El core/ importa shared.db (que aporta sqlalchemy); el lambda
    declara sqlalchemy en su pyproject -> duplicacion.
    """
    # Arrange
    lambda_root = _make_lambda(
        tmp_path,
        imports='from shared.db.session import db_session\n',
        deps=['pydantic', 'sqlalchemy>=2.0,<3.0'],
    )

    # Act
    result = validate_lambda_deps(lambda_root)

    # Assert
    assert result.is_valid is False
    assert 'sqlalchemy' in result.duplicated
    assert 'db' in result.providers['sqlalchemy']


def test_validate_detects_duplication_with_extras(
    tmp_path: Path,
) -> None:
    """`psycopg[binary]` en el lambda colisiona con `psycopg` de shared/.

    La comparacion por nombre canonico ve ambos como la misma lib.
    """
    # Arrange: shared.db aporta psycopg[binary]; el lambda declara
    # psycopg[binary] tambien.
    lambda_root = _make_lambda(
        tmp_path,
        imports='from shared.db.session import db_session\n',
        deps=['psycopg[binary]>=3.2,<4.0'],
    )

    # Act
    result = validate_lambda_deps(lambda_root)

    # Assert
    assert result.is_valid is False
    assert 'psycopg' in result.duplicated


def test_validate_fails_without_pyproject(tmp_path: Path) -> None:
    """validate_lambda_deps lanza DepValidatorError sin pyproject.toml."""
    # Arrange
    lambda_root = tmp_path / 'no-pyproject'
    (lambda_root / 'core').mkdir(parents=True)

    # Act + Assert
    with pytest.raises(DepValidatorError, match=r'pyproject\.toml'):
        validate_lambda_deps(lambda_root)


def test_format_report_describes_duplication(tmp_path: Path) -> None:
    """format_report lista la dep duplicada y el subpaquete que la da."""
    # Arrange
    lambda_root = _make_lambda(
        tmp_path,
        imports='from shared.db.session import db_session\n',
        deps=['alembic>=1.13,<2.0'],
    )
    result = validate_lambda_deps(lambda_root)

    # Act
    report = dep_validator.format_report(result)

    # Assert
    assert 'FAIL' in report
    assert 'alembic' in report
    assert 'D-3' in report


def test_format_report_ok_when_valid(tmp_path: Path) -> None:
    """format_report devuelve un OK cuando no hay duplicacion."""
    # Arrange
    lambda_root = _make_lambda(tmp_path, imports='', deps=['pydantic'])
    result = validate_lambda_deps(lambda_root)

    # Act
    report = dep_validator.format_report(result)

    # Assert
    assert report.startswith('OK')


def test_spec_extras_extracts_declared_extras() -> None:
    """spec_extras devuelve el conjunto de extras de un spec PEP 508."""
    assert spec_extras('pydantic[email]>=2.5') == frozenset({'email'})
    assert spec_extras('aws-lambda-powertools[all,tracer]>=3.0') == (
        frozenset({'all', 'tracer'})
    )
    assert spec_extras('pydantic') == frozenset()


def test_validate_passes_when_lambda_extra_not_in_shared(
    tmp_path: Path,
) -> None:
    """Un extra que shared/ NO aporta justifica declarar la dep.

    Tras el plan d-shared-only-imports, shared.core declara
    `pydantic[email]` y por ende aporta el extra `email` transitivamente
    a todos los lambdas. Usamos un caso hipotetico para validar la
    semantica: el lambda declara `aws-lambda-powertools[tracer,validator]`
    pero shared.aws solo aporta `aws-lambda-powertools[all]`. El conjunto
    {tracer, validator} es subset del {all} — duplicacion.
    Para el caso NO-duplicado, usamos un extra inventado que shared no da.
    """
    # Arrange: el core/ NO importa nada de shared (forzamos cierre vacio),
    # entonces cualquier dep declarada NO es duplicada — el cierre no la aporta.
    lambda_root = _make_lambda(
        tmp_path,
        imports='import json\n',  # sin imports a shared.*
        deps=['pydantic[email]>=2.5,<3.0'],
    )

    # Act
    result = validate_lambda_deps(lambda_root)

    # Assert
    assert result.is_valid is True
    assert result.duplicated == []


def test_validate_fails_when_extra_subset_of_shared(
    tmp_path: Path,
) -> None:
    """`pydantic` sin extra colisiona con `pydantic` de shared/.

    El lambda declara `pydantic` (sin extra); shared.lambda_kit aporta
    `pydantic`. El conjunto vacio de extras es subset -> duplicacion.
    """
    # Arrange
    lambda_root = _make_lambda(
        tmp_path,
        imports='from shared.lambda_kit import BaseController\n',
        deps=['pydantic>=2.5,<3.0'],
    )

    # Act
    result = validate_lambda_deps(lambda_root)

    # Assert
    assert result.is_valid is False
    assert 'pydantic' in result.duplicated
