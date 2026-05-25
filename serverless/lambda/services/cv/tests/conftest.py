"""Configuracion pytest del Lambda `cv`.

Agrega `core/` al `sys.path` y, si `shared/` no esta vendorizado, agrega
`serverless/lambda/` como fallback para que `import shared...` resuelva.
Setea env vars minimas para AppConfig.
"""

import os
import sys
from pathlib import Path

_LAMBDA_ROOT = Path(__file__).resolve().parent.parent
_CORE = _LAMBDA_ROOT / 'core'
sys.path.insert(0, str(_CORE))

if not (_CORE / 'shared').is_dir():
    _LAMBDA_BASE = _LAMBDA_ROOT.parents[1]
    sys.path.insert(0, str(_LAMBDA_BASE))

os.environ.setdefault('ENVIRONMENT', 'dev')
os.environ.setdefault('TESTING', '1')
os.environ.setdefault('SSM_NEON_URL_PATH', '/portfolio/dev/neon-url')
os.environ.setdefault('SSM_CACHE_TABLE_PATH', '/portfolio/dev/dynamodb/cache/name')
os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'cv-test')
os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'PortfolioTest')
