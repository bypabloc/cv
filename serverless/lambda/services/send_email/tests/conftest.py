"""Configuracion pytest del Lambda `send_email`.

Agrega `core/` al `sys.path` y, si `shared/` no esta vendorizado, agrega
`serverless/lambda/` como fallback para que `import shared...` resuelva.
Setea env vars minimas.
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
os.environ.setdefault(
    'SSM_EMAIL_CONFIG_TABLE_PATH', '/portfolio/dev/dynamodb/email-config/name'
)
os.environ.setdefault('EMAIL_FROM', 'no-reply@the-full-stack.com')
os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'send-email-test')
os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'PortfolioTest')
