# Fase C — shared.aws.ses + shared.aws.dynamodb_types

> shared.aws portador unico de boto3. Agrega `send_email(...)` helper en
> shared.aws.ses (hoy solo expone el cliente `ses`) y crea
> shared.aws.dynamodb_types con `TypeDeserializer` re-exportado.

## Contexto / Problema

- `contact_form/core/services/contact_service.py`:
  - L35: `import boto3`
  - L117-121: `_ses_client()` construye el cliente inline con
    `boto3.client('sesv2', region_name=...)` — no usa el singleton
    `shared.aws.ses.ses` (probablemente por compat con moto en tests).
  - L213: `_ses_client().send_email(FromEmailAddress=..., Destination=...,
    Content=...)`.
- `stream_processor/core/services/stream_service.py`:
  - L1: `from boto3.dynamodb.types import TypeDeserializer`
  - L33: `_deserializer = TypeDeserializer()`
  - L88: `_deserializer.deserialize(v)` en `deserialize_image()`.

## Solucion

### C.1 — `shared.aws.ses`: agregar helper `send_email(...)`

Estructura:

```python
# serverless/lambda/shared/aws/ses.py
from __future__ import annotations
import os
from typing import Any
import boto3

# Cliente module-scope (mantiene la API actual, NO se borra)
ses = boto3.client('sesv2', region_name=os.environ.get('AWS_SES_REGION', 'us-east-1'))


def _client() -> Any:
    """Devuelve un cliente sesv2 nuevo (lazy, compat con moto)."""
    return boto3.client(
        'sesv2', region_name=os.environ.get('AWS_SES_REGION', 'us-east-1')
    )


def send_email(
    *,
    from_address: str,
    to_addresses: list[str],
    subject: str,
    text_body: str,
    html_body: str | None = None,
    reply_to: list[str] | None = None,
) -> dict[str, Any]:
    """Envia un email via SES v2.

    Encapsula el patron `boto3.client('sesv2').send_email(...)` que
    contact_form duplicaba. Cliente lazy (no module-scope) para que moto
    lo intercepte en tests.

    Returns
    -------
    dict[str, Any]
        Response de SES (incluye `MessageId`).
    """
    body: dict[str, Any] = {'Text': {'Data': text_body, 'Charset': 'UTF-8'}}
    if html_body is not None:
        body['Html'] = {'Data': html_body, 'Charset': 'UTF-8'}

    request: dict[str, Any] = {
        'FromEmailAddress': from_address,
        'Destination': {'ToAddresses': to_addresses},
        'Content': {
            'Simple': {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': body,
            },
        },
    }
    if reply_to:
        request['ReplyToAddresses'] = reply_to

    return _client().send_email(**request)
```

Re-exportar en `shared/aws/__init__.py`:

```python
from shared.aws.ses import send_email, ses
```

### C.2 — `shared.aws.dynamodb_types`: nuevo modulo con `TypeDeserializer`

Estructura:

```python
# serverless/lambda/shared/aws/dynamodb_types.py
"""@module shared.aws.dynamodb_types — re-export limpio de boto3.dynamodb.types.

Aisla al stream_processor del import directo de boto3. Si en el futuro
hace falta TypeSerializer o helpers de conversion Decimal->str, viven
aqui.
"""
from __future__ import annotations
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

__all__ = ['TypeDeserializer', 'TypeSerializer']
```

Re-exportar en `shared/aws/__init__.py`:

```python
from shared.aws.dynamodb_types import TypeDeserializer, TypeSerializer
```

### C.3 — `shared/aws/__init__.py` actualizado

```python
from shared.aws.dynamodb import get_resource, get_table, reset_resource_cache
from shared.aws.dynamodb_types import TypeDeserializer, TypeSerializer
from shared.aws.ses import send_email, ses
from shared.aws.ssm import clear_cache, get_parameter, get_secret

__all__ = [
    'TypeDeserializer',
    'TypeSerializer',
    'clear_cache',
    'get_parameter',
    'get_resource',
    'get_secret',
    'get_table',
    'reset_resource_cache',
    'send_email',
    'ses',
]
```

## Archivos afectados

### Crear

- `serverless/lambda/shared/aws/dynamodb_types.py` — re-export de boto3.dynamodb.types.
  - Verificar: `python -c "from shared.aws import TypeDeserializer; d = TypeDeserializer(); print(d.deserialize({'S': 'x'}))"`.

### Modificar

- `serverless/lambda/shared/aws/ses.py` — agrega `send_email(...)` y `_client()` lazy.
  - Verificar: pytest del unit test nuevo (Fase E reemplaza contact_service).
- `serverless/lambda/shared/aws/__init__.py` — extiende re-exports y `__all__`.
  - Verificar: `python -c "from shared.aws import send_email, TypeDeserializer"`.

### Tests nuevos

- `serverless/lambda/shared/tests/unit/shared/aws/test_send_email_builds_request_correctly.py`
- `serverless/lambda/shared/tests/unit/shared/aws/test_send_email_with_html_body.py`
- `serverless/lambda/shared/tests/unit/shared/aws/test_send_email_with_reply_to.py`
- `serverless/lambda/shared/tests/unit/shared/aws/test_dynamodb_types_reexport.py`

Cada test, BDD docstring + assert exacto. Mockean `boto3.client` con `moto`
o `unittest.mock`.

## Criterios de aceptacion

- **AC-C1**: Given `shared.aws.send_email(from_address=..., to_addresses=[...],
  subject=..., text_body=...)`, When se invoca, Then construye el dict
  `request` con la estructura `Content.Simple.{Subject,Body.Text}` y llama
  al cliente sesv2.
- **AC-C2**: Given `html_body` no nulo, When se invoca `send_email`, Then el
  request incluye `Content.Simple.Body.Html`.
- **AC-C3**: Given `reply_to=['x@y.com']`, When se invoca, Then el request
  incluye `ReplyToAddresses`.
- **AC-C4**: Given `from shared.aws import TypeDeserializer`, When se invoca
  `TypeDeserializer().deserialize({'S': 'x'})`, Then retorna `'x'`.
- **AC-C5**: Given el `__init__.py` de shared.aws, When inspecciono `__all__`,
  Then contiene `send_email`, `TypeDeserializer`, `TypeSerializer` (ademas
  de los simbolos previos).

## Verificacion

```bash
python -m compileall -q serverless/lambda/shared/aws

python devtools/run.py serverless tests --type=unit --shared

python devtools/run.py serverless lint-deps
```

## Commit

```text
feat(shared/aws): agrega send_email helper y re-exporta TypeDeserializer

- shared/aws/ses.py: nueva funcion send_email(from_address, to_addresses,
  subject, text_body, html_body, reply_to) que encapsula el patron
  boto3.client('sesv2').send_email. Cliente lazy (compat con moto)
- shared/aws/dynamodb_types.py: nuevo modulo que re-exporta
  TypeDeserializer y TypeSerializer de boto3.dynamodb.types
- shared/aws/__init__.py: extiende __all__ con send_email,
  TypeDeserializer, TypeSerializer
- Tests unit en shared/tests/unit/shared/aws/ para los 4 escenarios
  nuevos (BDD docstring, asserts exactos)
- contact_form y stream_processor migran sus imports en Fase E
```
