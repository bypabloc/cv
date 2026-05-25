"""shared.lambda_kit.base_settings.BaseSettings.

Given una subclase con un campo str anotado y la env var seteada,
When se instancia,
Then el campo toma el valor de la env var homonima en MAYUSCULAS.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.base_settings import BaseSettings

pytestmark = pytest.mark.unit


def test_base_settings_loads_str_field_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv('REGION', 'us-east-1')

    class _Config(BaseSettings):
        region: str = ''

    # Act
    config = _Config()

    # Assert
    assert config.region == 'us-east-1'
