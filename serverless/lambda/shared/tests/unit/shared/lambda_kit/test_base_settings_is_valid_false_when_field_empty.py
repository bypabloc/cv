"""shared.lambda_kit.base_settings.BaseSettings.is_valid.

Given una config cuyo campo anotado quedo en string vacio,
When se invoca is_valid,
Then devuelve False.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.base_settings import BaseSettings

pytestmark = pytest.mark.unit


def test_base_settings_is_valid_false_when_field_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv('REGION', raising=False)

    class _Config(BaseSettings):
        region: str = ''

    config = _Config()

    # Act + Assert
    assert config.is_valid() is False
