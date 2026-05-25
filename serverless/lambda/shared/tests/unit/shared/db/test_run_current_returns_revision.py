"""shared.db.migrations.run_current.

Given una DB con una revision aplicada,
When se invoca run_current,
Then devuelve un dict con la revision actual.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from shared.db.migrations import run_current

pytestmark = pytest.mark.unit


def test_run_current_returns_revision() -> None:
    # Arrange + Act
    with patch(
        'shared.db.migrations.current_revision',
        return_value='81c2cc51db34',
    ):
        result = run_current()

    # Assert
    assert result == {'current': '81c2cc51db34'}
