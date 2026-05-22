"""Service db_service.current_revision.

Given una DB sin migrar (Alembic no imprime ninguna revision),
When se invoca current_revision,
Then captura la salida vacia de alembic.command.current y devuelve None.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_current_revision_returns_none_when_unmigrated():
    from services.db_service import current_revision

    # Arrange: build_config devuelve un Config falso; command.current no
    # escribe nada en el buffer -> _capture devuelve '' -> None.
    with (
        patch('services.db_service.build_config', return_value=object()),
        patch('services.db_service.command.current') as mock_current,
    ):
        # Act
        result = current_revision()

    # Assert
    assert mock_current.call_count == 1
    assert result is None
