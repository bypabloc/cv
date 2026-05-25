# 04 — Helper `shared/queue/` (publisher SQS)

> Subpaquete nuevo en `serverless/lambda/shared/queue/` con un publisher
> SQS minimal compartido por los 2 encoders. Resuelve la URL de la cola
> desde SSM (cached en cold start), serializa el payload a JSON y llama
> `boto3.client('sqs').send_message()`. Manejo de errores + metricas.

[< 03](03-devtools-extensions.md) | [Siguiente: 05 — contact_worker >](05-contact-worker.md)

---

## Estructura

```text
serverless/lambda/shared/queue/        ← NUEVO subpaquete
├── pyproject.toml                     # deps: boto3, aws-lambda-powertools
├── __init__.py                        # re-exports publicos
├── publisher.py                       # send_to_queue() helper
├── client.py                          # SQS client cached (module-scope)
└── tests/
    ├── __init__.py
    ├── conftest.py                    # moto + env vars
    ├── test_send_to_queue_serializes_payload.py
    ├── test_send_to_queue_resolves_url_from_ssm_in_cold_start.py
    ├── test_send_to_queue_reuses_client_on_warm_start.py
    └── test_send_to_queue_raises_on_send_failure.py
```

## Subpaquete `pyproject.toml`

```toml
# serverless/lambda/shared/queue/pyproject.toml
[project]
name = "portfolio-shared-queue"
version = "1.0.0"
description = "Helper SQS publisher para los encoders del portfolio."
requires-python = ">=3.13"
dependencies = [
  "boto3>=1.34",
  "aws-lambda-powertools[tracer,metrics]>=3.0",
]

[tool.shared]
internal-deps = ["shared.observability", "shared.aws"]

[dependency-groups]
dev = [
  "pytest>=8",
  "moto[sqs]>=5",
]
```

`shared/queue/` declara `internal-deps: shared.observability` (logger,
metrics) y `shared.aws` (ssm reader). Asi `shared_resolver.py` resuelve el
cierre transitivo cuando un encoder usa `shared.queue`.

## `client.py`

```python
"""@module client — cliente SQS cacheado para invocaciones warm.

El cliente boto3 SQS se crea UNA vez a module-scope (mismo patron que
shared.aws.ssm). Reutilizado entre invocaciones warm del mismo Lambda.
"""

import os
from functools import lru_cache

import boto3
from botocore.config import Config


@lru_cache(maxsize=1)
def get_sqs_client():
    """Devuelve un cliente boto3.client('sqs') cacheado.

    Region default: us-east-1 (override con AWS_REGION env var).
    Connection pooling: 10 (defecto boto3 es bajo para Lambdas).
    """
    region = os.environ.get('AWS_REGION', 'us-east-1')
    return boto3.client(
        'sqs',
        region_name=region,
        config=Config(
            retries={'max_attempts': 3, 'mode': 'standard'},
            connect_timeout=2,
            read_timeout=5,
        ),
    )
```

## `publisher.py`

```python
"""@module publisher — helper para encolar mensajes a SQS desde un encoder.

Resuelve la URL de la cola desde SSM (env var SSM_<NAME>_URL_PATH inyectada
por devtools). El path SSM se cachea durante el cold start; el SQS client
se cachea en module-scope.
"""

from __future__ import annotations

import json
import os
from typing import Any

from shared.aws.ssm import get_secret
from shared.observability.logger import logger
from shared.observability.metrics import metrics
from aws_lambda_powertools.metrics import MetricUnit

from .client import get_sqs_client


class QueuePublishError(Exception):
    """Falla al publicar un mensaje a SQS. El encoder debe propagar como 5xx."""

    def __init__(self, queue_short_name: str, cause: Exception) -> None:
        super().__init__(f'No se pudo publicar a {queue_short_name}: {cause}')
        self.queue_short_name = queue_short_name
        self.cause = cause


def _resolve_queue_url(short_name: str) -> str:
    """Resuelve la URL de SQS desde el SSM path inyectado por devtools.

    short_name: el nombre del subpaquete del catalogo (ej. 'contact-form',
    'tracking-events'). Se busca SSM_<UPPER_SNAKE>_QUEUE_URL_PATH:
      contact-form    -> SSM_CONTACT_FORM_QUEUE_URL_PATH
      tracking-events -> SSM_TRACKING_EVENTS_QUEUE_URL_PATH

    El valor del env var es el PATH SSM (no la URL); se hace get_secret
    para obtener la URL real.
    """
    env_var = f'SSM_{short_name.upper().replace("-", "_")}_QUEUE_URL_PATH'
    ssm_path = os.environ.get(env_var)
    if not ssm_path:
        raise RuntimeError(
            f'{env_var} no esta seteada. devtools debe inyectarla cuando '
            f'el manifest declara uses.queues con la cola correspondiente.'
        )
    return get_secret(ssm_path)


def send_to_queue(
    *,
    queue_short_name: str,
    payload: dict[str, Any],
    message_attributes: dict[str, Any] | None = None,
) -> str:
    """Encola un mensaje JSON a SQS.

    Parameters
    ----------
    queue_short_name : str
        Nombre corto del catalogo ('contact-form' | 'tracking-events').
    payload : dict
        Dict serializable a JSON. Se serializa con `json.dumps` sin
        ensure_ascii (UTF-8) y se envia como MessageBody.
    message_attributes : dict | None
        Atributos SQS opcionales (max 10). Util para filtering.

    Returns
    -------
    str
        El MessageId que SQS asigna.

    Raises
    ------
    QueuePublishError
        Si SQS rechaza el send (network, throttle, queue no existe).
    """
    sqs = get_sqs_client()
    queue_url = _resolve_queue_url(queue_short_name)

    body = json.dumps(payload, ensure_ascii=False, default=str)
    try:
        resp = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=body,
            MessageAttributes=message_attributes or {},
        )
    except Exception as exc:
        metrics.add_metric(
            name='QueuePublishFailed',
            unit=MetricUnit.Count,
            value=1,
        )
        logger.exception(
            'failed to publish message to SQS',
            extra={
                'queue': queue_short_name,
                # NUNCA logear el payload completo (puede tener email/PII)
                'payload_keys': sorted(payload.keys()),
            },
        )
        raise QueuePublishError(queue_short_name, exc) from exc

    message_id: str = resp['MessageId']
    metrics.add_metric(
        name='QueuePublishOk',
        unit=MetricUnit.Count,
        value=1,
    )
    logger.info(
        'message published to SQS',
        extra={
            'queue': queue_short_name,
            'message_id': message_id,
            'payload_keys': sorted(payload.keys()),
        },
    )
    return message_id
```

## `__init__.py`

```python
"""@package shared.queue — publisher SQS para los encoders."""

from .publisher import QueuePublishError, send_to_queue

__all__ = ['QueuePublishError', 'send_to_queue']
```

## Tests

### `conftest.py`

```python
import os
import pytest

@pytest.fixture(autouse=True)
def _aws_env(monkeypatch):
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')


@pytest.fixture
def sqs_with_queue():
    """Setup moto SQS con una cola fake + el SSM path correspondiente."""
    from moto import mock_aws
    with mock_aws():
        import boto3
        sqs = boto3.client('sqs', region_name='us-east-1')
        url = sqs.create_queue(QueueName='portfolio-test-queue')['QueueUrl']
        # SSM mock: el path apunta a la URL
        ssm = boto3.client('ssm', region_name='us-east-1')
        ssm.put_parameter(
            Name='/portfolio/test/sqs/test-queue/url',
            Value=url,
            Type='String',
        )
        yield {'sqs': sqs, 'url': url}
```

### `test_send_to_queue_serializes_payload.py`

```python
"""
Given un payload dict con campos primitivos,
When send_to_queue se invoca,
Then el MessageBody en SQS es exactamente json.dumps(payload, ensure_ascii=False).
"""

import json
import os

from shared.queue import send_to_queue


def test_send_to_queue_serializes_payload(sqs_with_queue, monkeypatch):
    # Arrange
    monkeypatch.setenv(
        'SSM_TEST_QUEUE_QUEUE_URL_PATH', '/portfolio/test/sqs/test-queue/url'
    )
    payload = {'contact_id': '0190abc-...', 'name': 'Juan', 'message': 'Hola, ñ y é'}

    # Act
    msg_id = send_to_queue(queue_short_name='test-queue', payload=payload)

    # Assert
    received = sqs_with_queue['sqs'].receive_message(
        QueueUrl=sqs_with_queue['url'], MaxNumberOfMessages=1
    )['Messages'][0]
    assert msg_id == received['MessageId']
    assert json.loads(received['Body']) == payload
```

### `test_send_to_queue_resolves_url_from_ssm_in_cold_start.py`

```python
"""
Given el cliente SQS y el SSM no fueron llamados antes,
When send_to_queue se invoca por primera vez,
Then SSM se invoca para resolver la URL de la cola.
"""
# Usa moto + assert sobre el numero de invocaciones del SSM client mock.
```

### `test_send_to_queue_reuses_client_on_warm_start.py`

```python
"""
Given send_to_queue ya fue invocado una vez,
When se invoca de nuevo (mismo contenedor warm),
Then get_sqs_client retorna el mismo objeto cliente (lru_cache).
"""

from shared.queue.client import get_sqs_client


def test_get_sqs_client_is_cached():
    a = get_sqs_client()
    b = get_sqs_client()
    assert a is b
```

### `test_send_to_queue_raises_on_send_failure.py`

```python
"""
Given el SQS client lanza una excepcion al send_message,
When send_to_queue se invoca,
Then re-lanza QueuePublishError envolviendo la causa.
"""

import pytest
from unittest.mock import patch

from shared.queue import QueuePublishError, send_to_queue


def test_send_to_queue_raises_queue_publish_error_on_send_failure(
    monkeypatch, sqs_with_queue
):
    monkeypatch.setenv(
        'SSM_TEST_QUEUE_QUEUE_URL_PATH', '/portfolio/test/sqs/test-queue/url'
    )
    with patch('shared.queue.client.get_sqs_client') as get_client:
        get_client.return_value.send_message.side_effect = Exception('throttle')
        with pytest.raises(QueuePublishError) as exc:
            send_to_queue(queue_short_name='test-queue', payload={'x': 1})
        assert exc.value.queue_short_name == 'test-queue'
        assert 'throttle' in str(exc.value)
```

## Reglas duras

- **SIEMPRE** el SQS client es module-scope (lru_cache). Cero overhead en
  invocaciones warm.
- **SIEMPRE** el payload se serializa con `default=str` para que datetime,
  UUID, Decimal, etc no rompan json.dumps.
- **SIEMPRE** los logs NO incluyen el `MessageBody` completo (puede tener
  email, mensaje del visitante). Solo `payload_keys` y `message_id`.
- **SIEMPRE** el error `QueuePublishError` envuelve la excepcion original
  para que el handler la traduzca a HTTP 500/502.
- **NUNCA** se reintenta dentro de `send_to_queue`. boto3 ya hace retry
  estandar (3 intentos). El encoder propaga el fallo al cliente.
- **NUNCA** usar `send_message_batch` aqui — cada encoder publica 1
  mensaje por invocacion. El batch es del WORKER (consumiendo SQS), no
  del producer.

## AC cubiertos

Indirectamente: este modulo es la primitiva que usan AC-1 (encolar
contact) y AC-6 (encolar tracking). Las verificaciones directas estan en
las fases 07/08.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Crear boto3.client en cada invocacion | Cold-start innecesario | module-scope + lru_cache |
| Logear el `MessageBody` | Posible PII (email, mensaje) | Solo `keys` + `message_id` |
| Hardcodear la cola URL | Drift con multi-stage | Resolver via SSM en cold start |
| Levantar Exception generica | El encoder no sabe que paso | QueuePublishError especifica |
| Reintentar dentro del helper | Duplica retry de boto3 | Confiar en boto3 + propagar |
| FIFO methods (MessageGroupId) | Cola es standard | NUNCA |

## Verificacion incremental

```bash
# Tests del subpaquete shared/queue/
python devtools/run.py serverless tests --type=unit --shared=queue
# (o, si la opcion --shared aun no existe en CLI):
cd serverless/lambda/shared/queue
.venv/bin/pytest tests/ -v

# Linting
cd serverless/lambda && ruff check shared/queue/
```

---

[< 03](03-devtools-extensions.md) | [Siguiente: 05 — contact_worker >](05-contact-worker.md)
