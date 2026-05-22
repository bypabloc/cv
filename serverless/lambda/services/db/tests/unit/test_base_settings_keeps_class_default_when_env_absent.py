"""Util base_settings.BaseSettings — default de clase sin env var.

Given una subclase con un campo anotado que tiene valor por defecto en la
     clase y NO tiene env var,
When se construye la instancia,
Then el campo conserva el valor por defecto declarado en la clase.
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_base_settings_keeps_class_default_when_env_absent():
    from utils.base_settings import BaseSettings

    class _DefaultSettings(BaseSettings):
        region: str = 'us-east-1'

    # Arrange + Act: REGION no esta en el entorno.
    env_without_region = {k: v for k, v in os.environ.items() if k != 'REGION'}
    with patch.dict(os.environ, env_without_region, clear=True):
        settings = _DefaultSettings()

    # Assert
    assert settings.region == 'us-east-1'
