"""Configuracion pytest del Lambda `analytics`.

Agrega `core/` al `sys.path` y, si `shared/` no esta vendorizado, agrega
`serverless/lambda/` como fallback para que `import shared...` resuelva.
Setea env vars minimas para AppConfig. Provee fixtures comunes para
mockear shared.db / shared.rate_limit / shared.cache y el auth_guard.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_LAMBDA_ROOT = Path(__file__).resolve().parent.parent
_CORE = _LAMBDA_ROOT / 'core'
sys.path.insert(0, str(_CORE))

if not (_CORE / 'shared').is_dir():
    _LAMBDA_BASE = _LAMBDA_ROOT.parents[1]
    sys.path.insert(0, str(_LAMBDA_BASE))

os.environ.setdefault('ENVIRONMENT', 'dev')
os.environ.setdefault('TESTING', '1')
os.environ.setdefault('JWT_ISSUER', 'portfolio-auth')
os.environ.setdefault('JWT_AUDIENCE', 'portfolio')
os.environ.setdefault('CORS_ALLOWED_ORIGINS', '*')
os.environ.setdefault('RATE_LIMIT_ENDPOINT', '/analytics')
os.environ.setdefault('SSM_NEON_URL_PATH', '/portfolio/dev/neon-url')
os.environ.setdefault('SSM_CACHE_TABLE_PATH', 'portfolio-cache-dev')
os.environ.setdefault(
    'SSM_RATE_LIMIT_RULES_TABLE_PATH', 'portfolio-rate-limit-rules-dev'
)
os.environ.setdefault(
    'SSM_RATE_LIMIT_BUCKETS_TABLE_PATH', 'portfolio-rate-limit-buckets-dev'
)
os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'analytics-test')
os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'PortfolioTest')


@pytest.fixture
def mock_db_session(mocker):
    """Mockea `shared.db.session.db_session` como context manager.

    Devuelve un MagicMock que actua de SQLAlchemy session: setear
    `session.scalar.side_effect = [...]` o `session.execute.return_value`
    en el test para dirigir el resultado de las queries.
    """
    session = MagicMock(name='SQLAlchemySession')
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch('shared.db.session.db_session', return_value=cm)
    return session


@pytest.fixture
def mock_check_or_raise(mocker):
    """Mockea el rate-limit guard en el namespace del controller base.

    `controllers._base` importa `guard as rate_limit_guard` desde
    `utils.rate_limit_guard`, asi que se patchea ahi (donde se usa)."""
    return mocker.patch('controllers._base.rate_limit_guard', return_value=None)


@pytest.fixture
def mock_require_auth(mocker):
    """Mockea el auth_guard (no-op) en el namespace del controller base.

    `controllers._base` importa `require_auth` desde `utils.auth_guard`,
    asi que se patchea ahi (donde se usa)."""
    return mocker.patch('controllers._base.require_auth', return_value=None)
