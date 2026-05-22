"""Util base_settings.BaseSettings — tipo de campo no soportado.

Given una subclase con un campo anotado de un tipo que no es str ni list
     y una env var para ese campo,
When se construye la instancia,
Then la carga automatica ignora ese campo (no setea el atributo desde la
     env var porque el tipo no es str ni list).
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_base_settings_ignores_unsupported_field_type():
    from utils.base_settings import BaseSettings

    class _IntFieldSettings(BaseSettings):
        port: int

    # Arrange: PORT esta en el entorno pero el tipo int no se soporta.
    env_clean = {k: v for k, v in os.environ.items() if k != 'PORT'}
    env_clean['PORT'] = '9970'
    with patch.dict(os.environ, env_clean, clear=True):
        settings = _IntFieldSettings()

    # Assert: el campo no se carga (tipo int no soportado).
    assert hasattr(settings, 'port') is False
