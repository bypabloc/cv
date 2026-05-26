"""
Given el lambda contact_form,
When importamos el modulo core.handler,
Then register_warmup se llama UNA SOLA VEZ con ['sqs', 'dynamodb', 'ssm']
durante el module-scope (no dentro del handler).
"""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_handler_calls_register_warmup_in_module_scope() -> None:
    """register_warmup invocado con la lista exacta del manifest, SOLO 1 vez."""
    # Arrange: sacar el modulo del cache para forzar re-import + medir
    # el side effect del module-scope.
    sys.modules.pop('core.handler', None)

    # Act
    with patch(
        'shared.lambda_kit.snap_start_warmup.register_warmup'
    ) as mock_warmup:
        import core.handler  # noqa: F401 — el side-effect es lo que medimos

    # Assert
    mock_warmup.assert_called_once_with(clients=['sqs', 'dynamodb', 'ssm'])
