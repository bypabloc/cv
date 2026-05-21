"""Service db_service.run_stamp.

Given un target a marcar,
When se invoca run_stamp,
Then llama a alembic.command.stamp con ese target y devuelve la revision
     resultante.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_stamp_service_runs_alembic_stamp():
    from services.db_service import run_stamp

    # Arrange
    with (
        patch('services.db_service.command.stamp') as mock_stamp,
        patch(
            'services.db_service.current_revision',
            return_value='81c2cc51db34',
        ),
    ):
        # Act
        result = run_stamp(target='head')

    # Assert
    assert mock_stamp.call_count == 1
    assert result == {'target': 'head', 'current': '81c2cc51db34'}
