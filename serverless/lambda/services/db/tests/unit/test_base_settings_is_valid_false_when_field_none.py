"""Util base_settings.BaseSettings.is_valid — campo con valor None.

Given una subclase con un campo anotado cuyo default de clase es None,
When se invoca is_valid sin env var para ese campo,
Then devuelve False porque el valor es None.
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_base_settings_is_valid_false_when_field_none():
    from utils.base_settings import BaseSettings

    class _NoneSettings(BaseSettings):
        optional_field: str = None  # type: ignore[assignment]

    # Arrange: sin OPTIONAL_FIELD en el entorno -> conserva el default None.
    env_clean = {k: v for k, v in os.environ.items() if k != 'OPTIONAL_FIELD'}
    with patch.dict(os.environ, env_clean, clear=True):
        settings = _NoneSettings()

    # Act
    result = settings.is_valid()

    # Assert
    assert result is False
