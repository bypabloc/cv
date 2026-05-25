"""Settings AppConfig — modo testing.

Given AppConfig con TESTING=1,
When se invoca is_testing,
Then devuelve True.
"""

import pytest

pytestmark = pytest.mark.unit


def test_app_config_is_testing(monkeypatch):
    monkeypatch.setenv('TESTING', '1')
    # Forzar reload del modulo settings.config para que AppConfig() relea el env.
    import importlib

    import settings.config as config_mod

    importlib.reload(config_mod)
    assert config_mod.app_config.is_testing() is True


def test_app_config_is_not_testing_by_default(monkeypatch):
    monkeypatch.setenv('TESTING', '0')
    import importlib

    import settings.config as config_mod

    importlib.reload(config_mod)
    assert config_mod.app_config.is_testing() is False
