"""Util base_settings.BaseSettings.is_valid — config completa.

Given una subclase con todos sus campos anotados cargados con valores no
     vacios,
When se invoca is_valid,
Then devuelve True.
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_base_settings_is_valid_true_when_fields_set():
    from utils.base_settings import BaseSettings

    class _CompleteSettings(BaseSettings):
        name: str = 'default'

    # Arrange
    with patch.dict(os.environ, {'NAME': 'portfolio-db'}):
        settings = _CompleteSettings()

    # Act
    result = settings.is_valid()

    # Assert
    assert result is True
