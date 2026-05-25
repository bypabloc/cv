"""shared.lambda_kit.base_settings.BaseSettings.

Given una instancia con campos cargados,
When se invoca to_dict,
Then devuelve solo los campos publicos, sin atributos privados.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.base_settings import BaseSettings

pytestmark = pytest.mark.unit


def test_base_settings_to_dict_excludes_private(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv('REGION', 'us-east-1')

    class _Config(BaseSettings):
        region: str = ''

    config = _Config()

    # Act
    result = config.to_dict()

    # Assert
    assert result == {'region': 'us-east-1'}
