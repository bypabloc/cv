"""shared.lambda_kit.dispatch.DispatchResult.

Given el dataclass DispatchResult,
When se construye con valores explicitos,
Then expone los 4 campos is_valid / data / code / stage.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.dispatch import DispatchResult

pytestmark = pytest.mark.unit


def test_dispatch_result_is_dataclass_with_fields() -> None:
    # Act
    result = DispatchResult(
        is_valid=True,
        data={'k': 'v'},
        code=0,
        stage='controller',
    )

    # Assert
    assert result.is_valid is True
    assert result.data == {'k': 'v'}
    assert result.code == 0
    assert result.stage == 'controller'
