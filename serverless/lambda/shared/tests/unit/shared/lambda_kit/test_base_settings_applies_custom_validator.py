"""shared.lambda_kit.base_settings.BaseSettings.

Given una subclase con un validador custom load_<campo>,
When se instancia,
Then el validador transforma el valor del campo.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.base_settings import BaseSettings

pytestmark = pytest.mark.unit


def test_base_settings_applies_custom_validator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv('NAME', 'pablo')

    class _Config(BaseSettings):
        name: str = ''

        def load_name(self, value: str) -> str:
            return value.upper()

    # Act
    config = _Config()

    # Assert
    assert config.name == 'PABLO'
