"""shared.lambda_kit.base_settings.BaseSettings.to_json.

Given una config con un campo poblado,
When se invoca to_json,
Then devuelve el JSON string de la config.
"""

from __future__ import annotations

import json

import pytest
from shared.lambda_kit.base_settings import BaseSettings

pytestmark = pytest.mark.unit


def test_base_settings_to_json_serializes_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv('REGION', 'us-east-1')

    class _Config(BaseSettings):
        region: str = ''

    config = _Config()

    # Act
    result = config.to_json()

    # Assert
    assert json.loads(result) == {'region': 'us-east-1'}
