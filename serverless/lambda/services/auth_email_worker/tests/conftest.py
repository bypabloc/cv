"""Configuracion pytest del Lambda `auth_email_worker`.

Agrega `core/` al `sys.path` para que los imports absolutos del codigo
del worker (`handler`, `controllers.`, `services.`, `models.`,
`settings.`, `shared.`) resuelvan en los tests.

La libreria comun `shared/` normalmente se vendoriza en `core/shared/`
por devtools antes de correr los tests (`serverless tests --type=unit`
lo hace). Si no esta vendorizada (pytest invocado directo), este
conftest agrega `serverless/lambda/` al path como fallback para que
`import shared...` resuelva desde la fuente maestra
`serverless/lambda/shared/`.

Setea las env vars minimas que `AppConfig` (settings/config.py) y el
codigo del worker necesitan para cargar sin un entorno Lambda real.
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
os.environ.setdefault('AWS_SES_REGION', 'us-east-1')
os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'auth-email-worker-test')
os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'PortfolioTest')
# Valores locales de los secretos (modo local: get_secret_by_name lee
# directo del env var en vez de SSM).
os.environ.setdefault('EMAIL_FROM', 'no-reply@example.com')
os.environ.setdefault(
    'DATABASE_URL',
    'postgresql://test:test@localhost/test',
)


@pytest.fixture(autouse=True)
def _aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setea credenciales AWS fake (autouse).

    Previene que boto3 lea ~/.aws/credentials reales o intente STS. Es
    necesario para que moto intercepte las llamadas en los tests que las
    usen.
    """
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
