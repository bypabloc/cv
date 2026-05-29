"""AppConfig — carga env vars + resuelve secretos lazy.

Cubre el ciclo basico del AppConfig: env vars con defaults, lazy
resolution de secretos via `get_secret_by_name`, lazy resolution de
nombres de tabla via SSM.

NO probamos cada cached_property (eso fija el resultado en la
instancia y rompe los siguientes tests). Probamos con instancias
nuevas.
"""

import os


def test_app_config_loads_env_vars_with_defaults():
    """Env vars basicas se cargan a la instancia."""
    from settings.config import AppConfig

    cfg = AppConfig()
    assert cfg.environment == 'dev'
    assert cfg.jwt_issuer == 'portfolio-auth'
    assert cfg.jwt_audience == 'portfolio'
    assert cfg.is_testing() is True


def test_app_config_jwt_secret_resolves_lazy(monkeypatch):
    """jwt_secret lee la env var JWT_SECRET en modo local."""
    from settings.config import AppConfig

    monkeypatch.setenv('JWT_SECRET', 'lazy-jwt-value')
    monkeypatch.delenv('SSM_JWT_SECRET_PATH', raising=False)

    cfg = AppConfig()
    assert cfg.jwt_secret == 'lazy-jwt-value'


def test_app_config_neon_url_resolves_lazy(monkeypatch):
    """neon_url lee la env var DB_URL en modo local."""
    from settings.config import AppConfig

    monkeypatch.setenv('DB_URL', 'postgresql://localhost/test')
    monkeypatch.delenv('SSM_NEON_URL_PATH', raising=False)

    cfg = AppConfig()
    assert cfg.neon_url == 'postgresql://localhost/test'


def test_app_config_ses_from_address_resolves_lazy(monkeypatch):
    from settings.config import AppConfig

    monkeypatch.setenv('SES_FROM_ADDRESS', 'no-reply@example.com')
    monkeypatch.delenv('SSM_SES_FROM_ADDRESS_PATH', raising=False)

    cfg = AppConfig()
    assert cfg.ses_from_address == 'no-reply@example.com'


def test_app_config_jwt_blacklist_table_uses_env_var(monkeypatch):
    """Si SSM_JWT_BLACKLIST_TABLE_PATH es un nombre plano (no `/`), se usa directo."""
    from settings.config import AppConfig

    monkeypatch.setenv(
        'SSM_JWT_BLACKLIST_TABLE_PATH',
        'portfolio-jwt-blacklist-test',
    )

    cfg = AppConfig()
    assert cfg.jwt_blacklist_table_name == 'portfolio-jwt-blacklist-test'


def test_app_config_resolves_table_from_ssm(monkeypatch):
    """Si SSM_*_PATH empieza con `/`, llama a get_parameter."""
    from settings import config as config_mod

    monkeypatch.setenv(
        'SSM_CACHE_TABLE_PATH',
        '/portfolio/dev/dynamodb/cache/name',
    )
    monkeypatch.setattr(
        config_mod,
        'get_parameter',
        lambda _path: 'portfolio-cache-dev',
    )

    cfg = config_mod.AppConfig()
    assert cfg.cache_table_name == 'portfolio-cache-dev'


def test_app_config_resolve_from_ssm_returns_empty_when_unset(monkeypatch):
    """Sin env var ni SSM path -> empty string."""
    from settings.config import AppConfig

    monkeypatch.delenv('SSM_AUTH_EMAIL_QUEUE_URL_PATH', raising=False)

    cfg = AppConfig()
    assert cfg.auth_email_queue_url == ''


def test_app_config_enums_present():
    """ErrorCode / LogMetricType estan exportados."""
    from settings.config import ErrorCode, LogMetricType

    assert ErrorCode.SUCCESS.value == 0
    assert ErrorCode.EMAIL_NOT_FOUND.value == 4001
    assert ErrorCode.TOKEN_REUSE_DETECTED.value == 4004
    assert LogMetricType.AUTH_LOGIN_OK.value == 'AUTH_LOGIN_OK'


def _silence_unused():
    """Avoid F401 / unused import for `os` (used implicitly via env)."""
    _ = os
