"""Util base_settings.BaseSettings.is_valid — campo string vacio.

Given una subclase con un campo anotado cargado con un string vacio,
When se invoca is_valid,
Then devuelve False porque el valor esta en blanco.
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_base_settings_is_valid_false_when_field_empty():
    from utils.base_settings import BaseSettings

    class _EmptySettings(BaseSettings):
        token: str = 'default'

    # Arrange
    with patch.dict(os.environ, {'TOKEN': '   '}):
        settings = _EmptySettings()

    # Act
    result = settings.is_valid()

    # Assert
    assert result is False
