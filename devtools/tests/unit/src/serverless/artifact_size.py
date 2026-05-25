"""Unit tests for serverless.artifact_size - control de peso del artefacto.

Path mirroring: devtools/serverless/artifact_size.py -> this file.

Verifica que el modulo mide el `build/` descomprimido y el `.zip`,
emite un WARN al 80% del limite de AWS Lambda y lanza
ArtifactTooLargeError al superar un hard limit (50 MB zip / 250 MB
descomprimido).
"""

from pathlib import Path

import pytest

from serverless.artifact_size import AWS_UNZIPPED_LIMIT_MB
from serverless.artifact_size import AWS_ZIP_LIMIT_MB
from serverless.artifact_size import ArtifactTooLargeError
from serverless.artifact_size import check_artifact_size
from serverless.artifact_size import format_size_report
from serverless.artifact_size import measure_artifact
from serverless.artifact_size import size_warning


pytestmark = pytest.mark.unit

_MB = 1024 * 1024


def test_measure_artifact_reports_unzipped_and_zip(tmp_path: Path) -> None:
    """measure_artifact devuelve el tamano del build/ y del .zip en MB."""
    # Arrange: build/ con un archivo de 2 MB
    build = tmp_path / 'build'
    build.mkdir()
    (build / 'big.bin').write_bytes(b'\0' * (2 * _MB))
    zip_path = tmp_path / 'build.zip'
    zip_path.write_bytes(b'\0' * (1 * _MB))

    # Act
    unzipped_mb, zip_mb = measure_artifact(build, zip_path)

    # Assert
    assert unzipped_mb == pytest.approx(2.0, abs=0.01)
    assert zip_mb == pytest.approx(1.0, abs=0.01)


def test_measure_artifact_zip_zero_when_absent(tmp_path: Path) -> None:
    """measure_artifact devuelve zip_mb 0.0 si el .zip no existe aun."""
    # Arrange
    build = tmp_path / 'build'
    build.mkdir()
    (build / 'code.py').write_bytes(b'\0' * _MB)

    # Act
    unzipped_mb, zip_mb = measure_artifact(build, zip_path=None)

    # Assert
    assert unzipped_mb == pytest.approx(1.0, abs=0.01)
    assert zip_mb == 0.0


def test_size_warning_none_when_artifact_small() -> None:
    """size_warning devuelve None cuando el artefacto esta holgado."""
    # Act
    warning = size_warning(unzipped_mb=100.0, zip_mb=30.0)

    # Assert
    assert warning is None


def test_size_warning_fires_at_80_percent_unzipped() -> None:
    """size_warning avisa cuando el descomprimido supera el 80%."""
    # Arrange: 210 MB > 80% de 250 MB
    over = AWS_UNZIPPED_LIMIT_MB * 0.85

    # Act
    warning = size_warning(unzipped_mb=over, zip_mb=10.0)

    # Assert
    assert warning is not None
    assert '[WARN]' in warning
    assert 'descomprimido' in warning


def test_size_warning_fires_at_80_percent_zip() -> None:
    """size_warning avisa cuando el .zip supera el 80%."""
    # Arrange: 45 MB > 80% de 50 MB
    over = AWS_ZIP_LIMIT_MB * 0.90

    # Act
    warning = size_warning(unzipped_mb=50.0, zip_mb=over)

    # Assert
    assert warning is not None
    assert 'zip' in warning


def test_size_warning_reports_both_figures() -> None:
    """El WARN incluye ambas cifras (descomprimido y zip)."""
    # Act
    warning = size_warning(unzipped_mb=210.0, zip_mb=45.0)

    # Assert
    assert warning is not None
    assert '210.0 MB' in warning
    assert '45.0 MB' in warning


def test_check_artifact_size_passes_under_limits() -> None:
    """check_artifact_size no lanza nada si el artefacto esta bajo limite."""
    # Act + Assert (no raise)
    check_artifact_size(unzipped_mb=100.0, zip_mb=20.0)


def test_check_artifact_size_aborts_on_unzipped_over_limit() -> None:
    """check_artifact_size aborta si el descomprimido supera 250 MB."""
    # Act + Assert
    with pytest.raises(ArtifactTooLargeError, match='descomprimido'):
        check_artifact_size(unzipped_mb=260.0, zip_mb=20.0)


def test_check_artifact_size_aborts_on_zip_over_limit() -> None:
    """check_artifact_size aborta si el .zip supera 50 MB."""
    # Act + Assert
    with pytest.raises(ArtifactTooLargeError, match='zip'):
        check_artifact_size(unzipped_mb=100.0, zip_mb=55.0)


def test_format_size_report_includes_both_limits() -> None:
    """format_size_report muestra ambas cifras contra sus limites AWS."""
    # Act
    report = format_size_report(unzipped_mb=120.5, zip_mb=33.2)

    # Assert
    assert '120.5 MB' in report
    assert str(AWS_UNZIPPED_LIMIT_MB) in report
    assert '33.2 MB' in report
    assert str(AWS_ZIP_LIMIT_MB) in report
