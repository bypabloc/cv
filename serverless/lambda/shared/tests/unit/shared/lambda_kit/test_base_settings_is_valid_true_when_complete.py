"""shared.lambda_kit.base_settings.BaseSettings.is_valid.

Given una config con todos los campos anotados poblados,
When se invoca is_valid,
Then devuelve True.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.base_settings import BaseSettings

pytestmark = pytest.mark.unit


def test_base_settings_is_valid_true_when_complete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv('REGION', 'us-east-1')

    class _Config(BaseSettings):
        region: str = ''

    config = _Config()

    # Act + Assert
    assert config.is_valid() is True
