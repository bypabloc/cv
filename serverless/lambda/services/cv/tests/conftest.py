"""Configuracion pytest del Lambda `cv`.

Agrega `core/` al `sys.path` y, si `shared/` no esta vendorizado, agrega
`serverless/lambda/` como fallback para que `import shared...` resuelva.
Setea env vars minimas para AppConfig (incluye las del dominio admin
content/publish absorbido de cv_admin: JWT, CORS del admin y secretos
locales fake).
"""

import os
import sys
from pathlib import Path

import pytest

_LAMBDA_ROOT = Path(__file__).resolve().parent.parent
_CORE = _LAMBDA_ROOT / 'core'
sys.path.insert(0, str(_CORE))

if not (_CORE / 'shared').is_dir():
    _LAMBDA_BASE = _LAMBDA_ROOT.parents[1]
    sys.path.insert(0, str(_LAMBDA_BASE))

os.environ.setdefault('ENVIRONMENT', 'dev')
os.environ.setdefault('TESTING', '1')
os.environ.setdefault('AWS_REGION', 'us-east-1')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
os.environ.setdefault('SSM_NEON_URL_PATH', '/portfolio/dev/neon-url')
os.environ.setdefault('SSM_CACHE_TABLE_PATH', '/portfolio/dev/dynamodb/cache/name')
os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'cv-test')
os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'PortfolioTest')
os.environ.setdefault('JWT_ISSUER', 'portfolio-auth')
os.environ.setdefault('JWT_AUDIENCE', 'portfolio')
os.environ.setdefault(
    'CORS_ALLOWED_ORIGINS',
    'https://admin.portfolio.dev.the-full-stack.com',
)

# Secretos locales (get_secret_by_name los lee del env var en modo local).
# Valores fake generados en runtime para evitar falsos positivos de
# scanners (GitGuardian) sobre placeholders literales.
import secrets as _secrets  # noqa: E402

os.environ.setdefault('JWT_SECRET', _secrets.token_urlsafe(48))
os.environ.setdefault('DB_URL', 'postgresql://test:test@localhost/test')
os.environ.setdefault('ADMIN_EMAILS', 'admin@example.com')
os.environ.setdefault('GITHUB_DEPLOY_TOKEN', _secrets.token_urlsafe(32))


@pytest.fixture(autouse=True)
def _aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setea credenciales AWS fake (autouse) para que boto3 no lea reales."""
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_REGION', 'us-east-1')


@pytest.fixture(autouse=True)
def _reset_admin_cache():
    """Resetea el cache de shared.auth.admin entre tests."""
    import shared.auth.admin as admin

    admin._CACHE.update({'emails': frozenset(), 'expires_at': 0.0})
    yield
    admin._CACHE.update({'emails': frozenset(), 'expires_at': 0.0})


@pytest.fixture
def app_config():
    """AppConfig limpio por test."""
    from settings.config import AppConfig

    return AppConfig()
