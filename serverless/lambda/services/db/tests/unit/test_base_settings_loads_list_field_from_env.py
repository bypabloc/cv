"""Util base_settings.BaseSettings — campo tipo list desde env var.

Given una subclase con un campo anotado como list[str] y una env var con
     valores separados por ', ',
When se construye la instancia,
Then el campo se carga como lista dividida por ', '.
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_base_settings_loads_list_field_from_env():
    from utils.base_settings import BaseSettings

    class _ListSettings(BaseSettings):
        origins: list[str]

    # Arrange + Act
    with patch.dict(os.environ, {'ORIGINS': 'a.com, b.com, c.com'}):
        settings = _ListSettings()

    # Assert
    assert settings.origins == ['a.com', 'b.com', 'c.com']
