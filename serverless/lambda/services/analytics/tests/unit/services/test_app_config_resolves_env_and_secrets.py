"""
Given el AppConfig del Lambda analytics,
When se leen sus campos, helpers y secretos lazy,
Then resuelve env vars, is_testing, _resolve_from_ssm (vacio/literal/path) y
  las @cached_property de secretos/tablas (mockeando SSM).
"""

import settings.config as config


def test_resolve_from_ssm_empty_literal_and_path(monkeypatch):
    # Vacio -> ''
    monkeypatch.delenv('SOME_TABLE_PATH', raising=False)
    assert config._resolve_from_ssm('SOME_TABLE_PATH') == ''

    # Literal (no empieza con '/') -> se usa tal cual.
    monkeypatch.setenv('SOME_TABLE_PATH', 'portfolio-cache-dev')
    assert config._resolve_from_ssm('SOME_TABLE_PATH') == 'portfolio-cache-dev'

    # Path SSM (empieza con '/') -> get_parameter.
    monkeypatch.setenv('SOME_TABLE_PATH', '/portfolio/dev/dynamodb/cache/name')
    monkeypatch.setattr(config, 'get_parameter', lambda p: f'resolved:{p}')
    assert config._resolve_from_ssm('SOME_TABLE_PATH') == (
        'resolved:/portfolio/dev/dynamodb/cache/name'
    )


def test_app_config_fields_helpers_and_lazy_secrets(monkeypatch):
    monkeypatch.setenv('TESTING', '1')
    monkeypatch.setenv('SSM_CACHE_TABLE_PATH', 'portfolio-cache-dev')
    monkeypatch.setenv(
        'SSM_RATE_LIMIT_RULES_TABLE_PATH', 'portfolio-rl-rules-dev'
    )
    monkeypatch.setenv(
        'SSM_RATE_LIMIT_BUCKETS_TABLE_PATH', 'portfolio-rl-buckets-dev'
    )
    monkeypatch.setattr(
        config, 'get_secret_by_name', lambda name, local_env=None: f'sec:{name}'
    )

    cfg = config.AppConfig()

    assert cfg.is_testing() is True
    assert cfg.jwt_issuer == 'portfolio-auth'
    assert cfg.jwt_audience == 'portfolio'
    assert cfg.rate_limit_endpoint == '/analytics'
    assert cfg.date_default_days == 30
    assert cfg.date_max_days == 90
    assert cfg.page_size_default == 50
    assert cfg.page_size_max == 200
    assert cfg.cache_ttl_aggregate == 60
    assert cfg.cache_ttl_live == 10
    # Secretos lazy (@cached_property).
    assert cfg.jwt_secret == 'sec:jwt-secret'
    assert cfg.neon_url == 'sec:neon-url'
    # Tablas resueltas (literal -> tal cual).
    assert cfg.cache_table_name == 'portfolio-cache-dev'
    assert cfg.rate_limit_rules_table_name == 'portfolio-rl-rules-dev'
    assert cfg.rate_limit_buckets_table_name == 'portfolio-rl-buckets-dev'
