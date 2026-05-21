"""Service db_service.run_current.

Given una DB con una revision aplicada,
When se invoca run_current,
Then devuelve esa revision en la clave 'current'.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_current_service_returns_revision():
    from services.db_service import run_current

    # Arrange
    with patch(
        'services.db_service.current_revision',
        return_value='81c2cc51db34',
    ):
        # Act
        result = run_current()

    # Assert
    assert result == {'current': '81c2cc51db34'}
