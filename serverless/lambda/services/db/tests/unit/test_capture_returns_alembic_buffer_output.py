"""Service db_service._capture.

Given un comando de Alembic que escribe en el buffer del Config,
When _capture ejecuta ese comando,
Then construye un Config ligado a un buffer, ejecuta la funcion y
     devuelve el texto capturado sin espacios al borde.
"""

import io
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_capture_returns_alembic_buffer_output():
    from services.db_service import _capture

    captured_buffers: list[io.StringIO] = []

    def fake_build_config(out: io.StringIO) -> io.StringIO:
        captured_buffers.append(out)
        return out

    def fake_command(cfg: io.StringIO) -> None:
        cfg.write('  rev1 -> rev2 (head)  ')

    # Arrange + Act
    with patch(
        'services.db_service.build_config', side_effect=fake_build_config
    ):
        result = _capture(fake_command)

    # Assert
    assert len(captured_buffers) == 1
    assert result == 'rev1 -> rev2 (head)'
