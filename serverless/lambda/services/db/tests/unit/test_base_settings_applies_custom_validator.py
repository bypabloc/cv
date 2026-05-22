"""Util base_settings.BaseSettings — validador custom load_<campo>.

Given una subclase con un campo y un metodo load_<campo> que lo
     transforma,
When se construye la instancia,
Then el validador custom se aplica sobre el valor cargado.
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_base_settings_applies_custom_validator():
    from utils.base_settings import BaseSettings

    class _ValidatedSettings(BaseSettings):
        level: str = 'info'

        def load_level(self, value: str) -> str:
            return value.upper()

    # Arrange + Act
    with patch.dict(os.environ, {'LEVEL': 'debug'}):
        settings = _ValidatedSettings()

    # Assert
    assert settings.level == 'DEBUG'
