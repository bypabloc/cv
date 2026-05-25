"""Settings config.AppConfig.is_testing — flag de modo testing.

Given una AppConfig con la env var TESTING en '1' y otra en '0',
When se invoca is_testing,
Then devuelve True cuando TESTING es '1' y False en cualquier otro caso.
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_app_config_is_testing_reflects_flag():
    from settings.config import AppConfig

    # Arrange + Act
    with patch.dict(os.environ, {'TESTING': '1'}):
        config_on = AppConfig()
    with patch.dict(os.environ, {'TESTING': '0'}):
        config_off = AppConfig()

    # Assert
    assert config_on.is_testing() is True
    assert config_off.is_testing() is False
