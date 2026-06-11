"""core.settings.config.AppConfig — secretos lazy + tablas desde SSM.

Given env vars con un path SSM, un valor plano y una ausente,
When se accede a los cached_property de AppConfig,
Then `_resolve_from_ssm` resuelve path -> get_parameter, plano -> directo,
ausente -> '', y los secretos delegan en get_secret_by_name con su
local_env correspondiente; `is_testing` refleja el flag.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_app_config_resolves_lazy_secrets_and_tables(monkeypatch) -> None:
    # Arrange
    from core.settings import config as config_module
    from core.settings.config import AppConfig

    monkeypatch.setenv(
        'SSM_JWT_BLACKLIST_TABLE_PATH', '/portfolio/dev/dynamodb/jwt/name'
    )
    monkeypatch.setenv('SSM_RATE_LIMIT_RULES_TABLE_PATH', 'tabla-plana')
    monkeypatch.delenv('SSM_RATE_LIMIT_BUCKETS_TABLE_PATH', raising=False)
    monkeypatch.setattr(
        config_module,
        'get_parameter',
        lambda path: f'resuelto:{path}',
    )
    monkeypatch.setattr(
        config_module,
        'get_secret_by_name',
        lambda name, local_env: f'{name}|{local_env}',
    )
    cfg = AppConfig()
    cfg.testing = '1'

    # Act / Assert
    assert (
        cfg.jwt_blacklist_table_name
        == 'resuelto:/portfolio/dev/dynamodb/jwt/name'
    )
    assert cfg.rate_limit_rules_table_name == 'tabla-plana'
    assert cfg.rate_limit_buckets_table_name == ''
    assert cfg.jwt_secret == 'jwt-secret|JWT_SECRET'
    assert cfg.neon_url == 'neon-url|DB_URL'
    assert cfg.is_testing() is True
