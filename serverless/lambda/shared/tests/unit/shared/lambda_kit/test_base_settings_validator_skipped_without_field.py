"""shared.lambda_kit.base_settings.BaseSettings.

Given una config con un metodo load_<X> cuyo campo X no esta anotado,
When se instancia,
Then el validador no se aplica (no hay campo X que setear).
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.base_settings import BaseSettings

pytestmark = pytest.mark.unit


def test_base_settings_validator_skipped_without_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv('REGION', 'us-east-1')

    class _Config(BaseSettings):
        region: str = ''

        def load_ghost(self, value: str) -> str:
            # 'ghost' no es un campo anotado: este validador se ignora.
            return value.upper()

    # Act
    config = _Config()

    # Assert
    assert config.region == 'us-east-1'
    assert not hasattr(config, 'ghost')
