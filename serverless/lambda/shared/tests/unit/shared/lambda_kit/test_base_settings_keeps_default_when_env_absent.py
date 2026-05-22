"""shared.lambda_kit.base_settings.BaseSettings.

Given una subclase con un campo que tiene valor por defecto y sin la
     env var en el entorno,
When se instancia,
Then el campo conserva su valor por defecto.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.base_settings import BaseSettings

pytestmark = pytest.mark.unit


def test_base_settings_keeps_default_when_env_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv('STAGE', raising=False)

    class _Config(BaseSettings):
        stage: str = 'dev'

    # Act
    config = _Config()

    # Assert
    assert config.stage == 'dev'
