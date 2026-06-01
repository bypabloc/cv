"""Configuracion pytest del Lambda `users`.

Agrega `core/` al `sys.path` para que los imports absolutos del codigo del
Lambda (`handler`, `controllers.`, `services.`, `models.`, `settings.`,
`shared.`) resuelvan en los tests. Si `shared/` no esta vendorizado en
`core/shared/`, agrega `serverless/lambda/` como fallback. Setea las env
vars minimas que `AppConfig` necesita para cargar sin un entorno Lambda
real.
"""

import os
import sys
from pathlib import Path

import pytest

# core/ al path: imports absolutos del codigo del Lambda.
_LAMBDA_ROOT = Path(__file__).resolve().parent.parent
_CORE = _LAMBDA_ROOT / 'core'
sys.path.insert(0, str(_CORE))

# Fallback para `import shared...` si no esta vendorizado en core/shared/.
if not (_CORE / 'shared').is_dir():
    _LAMBDA_BASE = _LAMBDA_ROOT.parents[1]
    sys.path.insert(0, str(_LAMBDA_BASE))

# Env vars minimas para que AppConfig cargue sin un entorno Lambda real.
os.environ.setdefault('ENVIRONMENT', 'dev')
os.environ.setdefault('TESTING', '1')
os.environ.setdefault('AWS_REGION', 'us-east-1')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'users-test')
os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'PortfolioTest')
os.environ.setdefault('JWT_ISSUER', 'portfolio-auth')
os.environ.setdefault('JWT_AUDIENCE', 'portfolio')
os.environ.setdefault(
    'CORS_ALLOWED_ORIGINS',
    'https://admin.portfolio.dev.the-full-stack.com',
)
os.environ.setdefault(
    'USERS_BASE_URL',
    'https://api.portfolio.dev.the-full-stack.com/users',
)
# Nombre de la Lambda send_email (devtools lo inyecta desde uses.invokes
# en runtime; en tests un placeholder basta — el invoke se mockea).
os.environ.setdefault(
    'LAMBDA_SEND_EMAIL_FUNCTION_NAME', 'portfolio-send-email-test'
)

# Secretos locales (get_secret_by_name los lee del env var en modo local).
# Valores fake generados en runtime para evitar falsos positivos de
# scanners (GitGuardian) sobre placeholders literales.
import secrets as _secrets  # noqa: E402

os.environ.setdefault('JWT_SECRET', _secrets.token_urlsafe(48))
os.environ.setdefault('DB_URL', 'postgresql://test:test@localhost/test')
os.environ.setdefault('ADMIN_EMAILS', 'admin@example.com')


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
