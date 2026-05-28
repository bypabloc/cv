"""Configuracion pytest del Lambda `auth`.

Agrega `core/` al `sys.path` para que los imports absolutos del codigo
del Lambda (`handler`, `controllers.`, `services.`, `models.`,
`settings.`, `shared.`) resuelvan en los tests.

La libreria comun `shared/` normalmente se vendoriza en `core/shared/`
por devtools antes de correr los tests (`serverless tests --type=unit`
lo hace). Si no esta vendorizada (pytest invocado directo), este
conftest agrega `serverless/lambda/` al path como fallback para que
`import shared...` resuelva desde la fuente maestra
`serverless/lambda/shared/`.

Setea las env vars minimas que `AppConfig` (settings/config.py) y el
codigo del Lambda necesitan para cargar sin un entorno Lambda real.
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
# La fuente maestra shared/ vive en serverless/lambda/ (parents[1]:
# <lambda>/ -> services/ -> lambda/).
if not (_CORE / 'shared').is_dir():
    _LAMBDA_BASE = _LAMBDA_ROOT.parents[1]
    sys.path.insert(0, str(_LAMBDA_BASE))

# Env vars minimas para que AppConfig cargue sin un entorno Lambda real.
os.environ.setdefault('ENVIRONMENT', 'dev')
os.environ.setdefault('TESTING', '1')
os.environ.setdefault('AWS_REGION', 'us-east-1')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'auth-test')
os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'PortfolioTest')
os.environ.setdefault('JWT_ISSUER', 'portfolio-auth')
os.environ.setdefault('JWT_AUDIENCE', 'portfolio')
os.environ.setdefault(
    'MAGIC_LINK_BASE_URL',
    'https://api.portfolio.dev.the-full-stack.com/auth',
)
os.environ.setdefault(
    'DASHBOARD_CALLBACK_URL',
    'https://admin.portfolio.dev.the-full-stack.com/callback',
)
os.environ.setdefault(
    'CORS_ALLOWED_ORIGINS',
    'https://admin.portfolio.dev.the-full-stack.com',
)
# Secretos locales (get_secret_by_name los lee directo del env var en
# modo local cuando SSM_<UPPER>_PATH no esta seteado).
os.environ.setdefault('JWT_SECRET', 'test-jwt-secret-with-enough-length-1234567890')
os.environ.setdefault('TURNSTILE_SECRET_KEY', 'test-turnstile-secret')
os.environ.setdefault('TURNSTILE_BYPASS_SECRET', 'test-bypass-secret')
os.environ.setdefault(
    'DB_URL',
    'postgresql://test:test@localhost/test',
)
os.environ.setdefault('SES_FROM_ADDRESS', 'no-reply@example.com')


@pytest.fixture(autouse=True)
def _aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setea credenciales AWS fake (autouse).

    Previene que boto3 lea ~/.aws/credentials reales o intente STS.
    """
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_REGION', 'us-east-1')


@pytest.fixture
def app_config():
    """Singleton AppConfig limpio por test."""
    from settings.config import AppConfig
    return AppConfig()
