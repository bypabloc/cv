# Fase B: SnapStart warmup hook generico

## Objetivo

Crear `shared/lambda_kit/snap_start_warmup.py` con la API `register_warmup(
clients)`, que al invocarse en module-scope durante el INIT del lambda
pre-calienta handshakes TLS de los clientes boto3 indicados. El snapshot
SnapStart captura los clientes con sus conexiones HTTPS abiertas, y
post-restore la primera invocacion reutiliza el handshake (ahorra
~200-500ms por servicio).

## Estado actual

Hoy NO existe ningun hook de SnapStart warmup en este repo. Las lambdas
con `snap_start: true` (solo `contact_form` por ahora) restauran el cliente
boto3 pero pagan el handshake TLS en la PRIMERA llamada post-restore.

## API publica

```python
# Uso desde un lambda (module-scope, NO dentro del handler):
from shared.lambda_kit.snap_start_warmup import register_warmup

register_warmup(clients=['sqs', 'dynamodb', 'ssm'])

# Luego el handler normal:
def lambda_handler(event, context):
    ...
```

`clients` es una lista de strings con nombres de servicios AWS soportados.
Lista cerrada (validacion en runtime):

| Client | Warmup call | Permiso IAM requerido |
|--------|-------------|------------------------|
| `sqs` | `sqs.list_queues(MaxResults=1)` | `sqs:ListQueues` (account-wide, ya lo tiene cualquier rol AWS) |
| `dynamodb` | `dynamodb.describe_endpoints()` | ninguno (describe_endpoints es publico) |
| `ssm` | `ssm.list_parameters(MaxResults=1)` | `ssm:DescribeParameters` (account-wide, default) |
| `ses` | `sesv2.list_email_identities(PageSize=1)` | `ses:ListEmailIdentities` (account-wide, default) |
| `kms` | `kms.list_keys(Limit=1)` | `kms:ListKeys` (account-wide, default) |

**NO** se incluye `s3`, `lambda`, `logs`, etc. — agregar bajo demanda.

## Implementacion

```python
"""SnapStart warmup hook generico para lambdas Python con snap_start=true.

Pre-calienta handshakes TLS de los clientes boto3 indicados ANTES de que
SnapStart tome el snapshot. El snapshot Firecracker captura el cliente
con su conexion HTTPS abierta + cert chain verificado. Post-restore, la
primera invocacion reutiliza esa conexion: handshake ya hecho, gana
200-500ms por servicio AWS.

Uso (module-scope del handler, NO dentro del handler):

    from shared.lambda_kit.snap_start_warmup import register_warmup
    register_warmup(clients=['sqs', 'dynamodb', 'ssm'])

Soporta: sqs, dynamodb, ssm, ses, kms.

Cada warmup call corre con try/except: si falla (AWS 5xx transitorio,
permisos IAM faltantes), loguea WARNING y continua. NUNCA aborta el INIT.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable

import boto3
from botocore.config import Config


# Logger basico (NO usa shared.observability.logger porque ese tiene
# dependencias de Powertools que pueden no estar listas en module-scope
# muy temprano del INIT). En su lugar, usa logging stdlib que es siempre
# safe.
_logger = logging.getLogger('snap_start_warmup')


# Calls de warmup soportados. Cada uno hace handshake TLS + sigv4 sin
# tocar recursos del proyecto.
_WARMUP_CALLS: dict[str, Callable[[Any], Any]] = {
    'sqs': lambda c: c.list_queues(MaxResults=1),
    'dynamodb': lambda c: c.describe_endpoints(),
    'ssm': lambda c: c.describe_parameters(MaxResults=1),
    'ses': lambda c: c.list_email_identities(PageSize=1),
    'kms': lambda c: c.list_keys(Limit=1),
}


def _build_client(service: str, region: str) -> Any:
    """boto3.client con timeouts conservadores (NO debe colgar el INIT)."""
    return boto3.client(
        service if service != 'ses' else 'sesv2',
        region_name=region,
        config=Config(
            retries={'max_attempts': 1, 'mode': 'standard'},
            connect_timeout=3,
            read_timeout=3,
        ),
    )


def register_warmup(clients: list[str]) -> None:
    """Pre-calienta handshakes TLS de los clientes boto3 indicados.

    Args:
        clients: lista de servicios soportados (sqs, dynamodb, ssm, ses, kms).

    Raises:
        ValueError: si algun client no esta soportado (defensa contra typo
            en el manifest del lambda). Se levanta ANTES de hacer cualquier
            call AWS — defensa de fail-fast.

    Notes:
        - Llama SOLO desde module-scope del handler del lambda.
        - Cada warmup call tiene try/except: si falla, loguea WARNING y
          continua con los demas.
        - Si la lista esta vacia, no-op silencioso.
    """
    if not clients:
        return

    # Defensa fail-fast: typo en manifest aborta INIT con error claro.
    unsupported = [c for c in clients if c not in _WARMUP_CALLS]
    if unsupported:
        raise ValueError(
            f'snap_start_warmup: clientes no soportados: {unsupported}. '
            f'Soportados: {sorted(_WARMUP_CALLS)}'
        )

    region = os.environ.get('AWS_REGION', 'us-east-1')

    for client_name in clients:
        warmup_call = _WARMUP_CALLS[client_name]
        try:
            start = time.perf_counter()
            client = _build_client(client_name, region)
            warmup_call(client)
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            _logger.info(
                '[snap_start_warmup] %s: ok (%dms)', client_name, elapsed_ms,
            )
        except Exception as exc:  # noqa: BLE001 — fail-safe deliberado
            _logger.warning(
                '[snap_start_warmup] %s: failed (%s: %s)',
                client_name,
                type(exc).__name__,
                exc,
            )
```

## Tests TDD

### Test 1: warmup OK (AC-2)

```python
def test_register_warmup_logs_ok_when_all_clients_succeed(caplog):
    """
    Given los 3 clients (sqs, dynamodb, ssm) responden exito,
    When register_warmup(['sqs', 'dynamodb', 'ssm']) corre,
    Then loguea 3 lineas INFO con prefijo [snap_start_warmup] X: ok.
    """
    from unittest.mock import patch, MagicMock

    mock_client = MagicMock()
    mock_client.list_queues.return_value = {'QueueUrls': []}
    mock_client.describe_endpoints.return_value = {'Endpoints': []}
    mock_client.describe_parameters.return_value = {'Parameters': []}

    with patch('shared.lambda_kit.snap_start_warmup._build_client', return_value=mock_client):
        with caplog.at_level('INFO', logger='snap_start_warmup'):
            from shared.lambda_kit.snap_start_warmup import register_warmup
            register_warmup(['sqs', 'dynamodb', 'ssm'])

    ok_logs = [r for r in caplog.records if 'ok' in r.message]
    assert len(ok_logs) == 3
    assert any('sqs: ok' in r.message for r in ok_logs)
    assert any('dynamodb: ok' in r.message for r in ok_logs)
    assert any('ssm: ok' in r.message for r in ok_logs)
```

### Test 2: warmup parcial fail (AC-3)

```python
def test_register_warmup_continues_when_one_client_fails(caplog):
    """
    Given dynamodb falla con BotoCoreError pero sqs y ssm exito,
    When register_warmup(['sqs', 'dynamodb', 'ssm']) corre,
    Then loguea WARNING para dynamodb, INFO para sqs+ssm, completa sin raise.
    """
    from botocore.exceptions import BotoCoreError

    def build_client_factory(service: str, _region: str):
        c = MagicMock()
        if service == 'dynamodb':
            c.describe_endpoints.side_effect = BotoCoreError()
        else:
            c.list_queues.return_value = {'QueueUrls': []}
            c.describe_parameters.return_value = {'Parameters': []}
        return c

    with patch('shared.lambda_kit.snap_start_warmup._build_client', side_effect=build_client_factory):
        with caplog.at_level('WARNING', logger='snap_start_warmup'):
            from shared.lambda_kit.snap_start_warmup import register_warmup
            register_warmup(['sqs', 'dynamodb', 'ssm'])  # NO debe raise

    warnings = [r for r in caplog.records if r.levelname == 'WARNING']
    assert len(warnings) == 1
    assert 'dynamodb' in warnings[0].message
    assert 'failed' in warnings[0].message
```

### Test 3: typo en client (defensa fail-fast)

```python
def test_register_warmup_raises_on_unsupported_client():
    """
    Given un client no soportado en la lista,
    When register_warmup(['s3']) corre (s3 no esta en _WARMUP_CALLS),
    Then raise ValueError ANTES de cualquier call AWS.
    """
    from shared.lambda_kit.snap_start_warmup import register_warmup

    with pytest.raises(ValueError, match=r'no soportados.*s3'):
        register_warmup(['sqs', 's3'])
```

### Test 4: lista vacia (no-op)

```python
def test_register_warmup_empty_list_is_noop():
    """
    Given lista vacia,
    When register_warmup([]) corre,
    Then no-op silencioso (no falla, no llama boto3).
    """
    from unittest.mock import patch
    from shared.lambda_kit.snap_start_warmup import register_warmup

    with patch('shared.lambda_kit.snap_start_warmup._build_client') as mock_build:
        register_warmup([])
        mock_build.assert_not_called()
```

## IAM impact

Los warmup calls son **read-only y account-wide**. La mayoria de roles
Lambda ya los tienen implicitos:

| Call | IAM permission |
|------|----------------|
| `sqs:ListQueues` | YA en cualquier rol AWS default (no scoped) |
| `dynamodb:DescribeEndpoints` | No requiere permission (es publico) |
| `ssm:DescribeParameters` | YA en cualquier rol AWS default (no scoped) |

**NO se necesita agregar permisos IAM** al rol del lambda. El warmup hook
es transparente desde el punto de vista de IAM.

Si en el futuro el rol del lambda esta MUY estricto (least-privilege total)
y rechaza los warmup calls, el `try/except` lo loguea como WARNING y la
lambda funciona normal — solo pierde el speedup.

## Verificacion

```bash
# Unit tests del modulo nuevo
python devtools/run.py serverless tests --type=unit --shared

# Smoke test desde un lambda real: deployar contact_form con el hook
# activado y leer los logs cold start. Debe aparecer:
#   [snap_start_warmup] sqs: ok (XXXms)
#   [snap_start_warmup] dynamodb: ok (XXXms)
#   [snap_start_warmup] ssm: ok (XXXms)
# justo despues del RESTORE_REPORT.
```
