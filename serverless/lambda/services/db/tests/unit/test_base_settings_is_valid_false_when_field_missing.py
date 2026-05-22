"""Util base_settings.BaseSettings.is_valid — campo sin valor.

Given una subclase con un campo anotado que no tiene env var ni default,
When se invoca is_valid,
Then devuelve False porque falta el atributo.
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_base_settings_is_valid_false_when_field_missing():
    from utils.base_settings import BaseSettings

    class _IncompleteSettings(BaseSettings):
        required_field: str

    # Arrange: REQUIRED_FIELD no esta en el entorno; sin default.
    env_clean = {k: v for k, v in os.environ.items() if k != 'REQUIRED_FIELD'}
    with patch.dict(os.environ, env_clean, clear=True):
        settings = _IncompleteSettings()

    # Act
    result = settings.is_valid()

    # Assert
    assert result is False
