# 05 — Worker `contact_worker` (SQS -> Neon + SES)

> Nuevo Lambda `contact_worker` que consume la cola SQS
> `portfolio-contact-form-${stage}` (batch=1), persiste el contact en Neon
> (con `ON CONFLICT id DO NOTHING`) y envia el email al owner via SES.
> Sigue el patron `lambda-controller`.

[< 04](04-shared-queue-publisher.md) | [Siguiente: 06 — tracking_worker >](06-tracking-worker.md)

---

## Estructura del Lambda

```text
serverless/lambda/services/contact_worker/
├── manifest.yaml
├── pyproject.toml
├── .gitignore
├── uv.lock
├── core/
│   ├── __init__.py
│   ├── handler.py                       # SQS event router
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── worker/
│   │       ├── __init__.py
│   │       └── process.py               # operation=worker, action=process
│   ├── services/
│   │   ├── __init__.py
│   │   └── persistence.py               # save_contact + send_owner_email
│   ├── models/
│   │   ├── __init__.py
│   │   └── message.py                   # ContactQueueMessage Pydantic model
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── config.py                    # AppConfig + ErrorCode + logger
│   │   └── operations.py                # OPERATIONS dict
│   └── templates/
│       ├── owner_email.html             # COPIA de contact_form (NO mover)
│       └── owner_email.txt
├── events/
│   ├── sample_message.json              # event SQS de ejemplo
│   └── sample_batch.json
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── integration/                     # E2E con Neon de test
    │   ├── __init__.py
    │   ├── conftest.py
    │   ├── _fixtures/
    │   ├── test_process_message_persists_contact_e2e.py
    │   ├── test_idempotent_on_duplicate_message_id_e2e.py
    │   └── test_email_failure_marks_batch_item_failure_e2e.py
    └── unit/
        ├── __init__.py
        ├── _helpers.py
        ├── test_handler_returns_no_failures_on_success.py
        ├── test_handler_marks_failed_items_when_persistence_throws.py
        ├── test_handler_marks_failed_items_when_email_throws.py
        ├── test_process_controller_persists_and_emails.py
        ├── test_process_controller_idempotent_on_conflict.py
        └── test_message_model_rejects_invalid_uuid.py
```

> Nota: `templates/owner_email.{html,txt}` se DUPLICAN del `contact_form`.
> NO se mueven a `shared/` porque (a) son del dominio del worker, (b) son
> chicos, (c) duplicar es menos riesgoso que el packaging selectivo del
> deploy. Si crece, se evalua mover a `shared/templates/`.

## `manifest.yaml`

```yaml
# Manifiesto del Lambda contact_worker.
# Worker SQS-driven: consume mensajes de portfolio-contact-form-${stage}
# y persiste a Neon + manda email SES.

name: contact-worker
description: Procesa mensajes SQS de la cola contact-form (Neon + SES).

runtime: python3.13
handler: core.handler.lambda_handler
memory: 512       # MB — SES + Neon necesitan headroom
timeout: 30       # segundos — visibility_timeout=180 = 6x timeout

trigger:
  type: sqs
  queue: portfolio-contact-form-${stage}
  batch_size: 1
  function_response_types:
    - ReportBatchItemFailures

uses:
  queues:
    - { name: portfolio-contact-form-${stage}, access: consumer }
  tables:
    cache: read-write           # @cached para SSM
  secrets:
    - neon-url                   # connection string Neon
    - owner-email                # destinatario
    - ses-from-address           # remitente verificado
  sends-email: true

env:
  default:
    LOG_LEVEL: INFO
    AWS_SES_REGION: us-east-1
  dev:
    LOG_LEVEL: INFO
  stage:
    LOG_LEVEL: INFO
  prod:
    LOG_LEVEL: WARNING
```

## `core/handler.py`

```python
"""Lambda contact_worker — consume SQS portfolio-contact-form-${stage}.

Entrypoint del worker. Itera los Records del evento SQS y delega cada
mensaje al controller worker/process. Devuelve `batchItemFailures` para
los items que fallaron (SQS los reintenta hasta max_receive_count=3,
despues van a la DLQ).

El handler es delgado: NO contiene logica de negocio (que vive en
core/services/persistence.py).

Handler de la funcion AWS: `core.handler.lambda_handler`.
"""

from __future__ import annotations

import json
import os
import sys

_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from typing import Any

from settings.operations import OPERATIONS
from shared.lambda_kit import build_event_model, run_controller
from shared.observability.logger import logger
from shared.observability.metrics import metrics
from shared.observability.tracer import tracer
from aws_lambda_powertools.metrics import MetricUnit

__version__ = '1.0.0'

_EVENT_MODEL = build_event_model(OPERATIONS)


@logger.inject_lambda_context(
    log_event=False, correlation_id_path='requestContext.requestId'
)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Procesa un batch SQS (batch_size=1 en este worker).

    Returns
    -------
    dict
        `{'batchItemFailures': [{'itemIdentifier': <messageId>}, ...]}`.
        Si la lista esta vacia, SQS borra todos los mensajes del batch.
    """
    failures: list[dict[str, str]] = []
    records = event.get('Records', [])

    for record in records:
        message_id = record['messageId']
        try:
            body = json.loads(record['body'])
            run_controller(
                {'operation': 'worker', 'action': 'process', 'data': body},
                event_model=_EVENT_MODEL,
            )
            metrics.add_metric(name='ContactProcessed', unit=MetricUnit.Count, value=1)
        except Exception as exc:
            metrics.add_metric(name='ContactProcessFailed', unit=MetricUnit.Count, value=1)
            logger.exception(
                'failed to process contact message',
                extra={'message_id': message_id, 'error': str(exc)},
            )
            failures.append({'itemIdentifier': message_id})

    return {'batchItemFailures': failures}


_ = OPERATIONS
```

## `core/models/message.py`

```python
"""@module message — esquema del mensaje SQS del worker."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal


class ContactQueueMessage(BaseModel):
    """Mensaje SQS que la Lambda contact_form encola al worker.

    Schema versionado: si cambia, bump `schema_version` y el worker
    soporta multiples versiones por compatibilidad backward durante el
    rollout.
    """
    model_config = ConfigDict(extra='forbid')

    schema_version: Literal[1] = 1

    # IDs pre-generados por el encoder
    contact_id: str                                 # UUIDv7
    created_at: datetime
    session_id: str                                 # del visitante (resuelto en encoder)

    # Campos del form (ya validados por el encoder)
    name: str
    email: EmailStr
    message: str
    company: str | None = None
    role: str | None = None
    service_type: str | None = None
    budget: str | None = None
    timeline: str | None = None
    niche: str | None = None

    # Metadata del request HTTP (para ensure_session_and_visit)
    ip: str
    country: str | None = None
    user_agent: str | None = None
    origin_niche: str | None = None
```

## `core/settings/operations.py`

```python
"""@module operations — registro de operations del worker."""

OPERATIONS = {
    'worker': {
        'process': 'controllers.worker.process.Process',
    },
}
```

## `core/controllers/worker/process.py`

```python
"""Controller worker/process — procesa un mensaje SQS del contact_worker.

Orquesta: valida mensaje (Pydantic) -> persiste a Neon -> envia email.
Es idempotente: si el mensaje se procesa 2 veces, el INSERT a Neon es
no-op (`ON CONFLICT (id) DO NOTHING`) y el email NO se envia 2 veces (lo
controla el helper de persistence que retorna `persisted=False` cuando
el row ya existia).
"""

from __future__ import annotations

from models.message import ContactQueueMessage
from services.persistence import save_contact_idempotent, send_owner_email_safe
from settings.config import ErrorCode, logger
from shared.lambda_kit import BaseController


class Process(BaseController):
    """action = 'process'. Procesa 1 mensaje del worker."""

    event_model = ContactQueueMessage

    def execute(self) -> dict:
        data: ContactQueueMessage = self.validated_data

        # 1. Persistir contact (idempotente)
        result = save_contact_idempotent(data)

        if not result['persisted']:
            logger.info(
                'contact already persisted, skipping email',
                extra={'contact_id': data.contact_id},
            )
            return {
                'is_valid': True,
                'data': {'contact_id': data.contact_id, 'skipped': True},
                'code': 0,
            }

        # 2. Enviar email (si falla, se propaga -> handler marca batchItemFailure)
        send_owner_email_safe(data, result)

        return {
            'is_valid': True,
            'data': {'contact_id': data.contact_id, 'persisted': True},
            'code': 0,
        }
```

## `core/services/persistence.py`

```python
"""@module persistence — UPSERT + INSERT idempotente + email SES.

Spec: el contact se persiste con `ON CONFLICT (id) DO NOTHING`. El
helper `save_contact_idempotent` retorna `persisted=True` si la fila se
inserto, `persisted=False` si ya existia (idempotencia). El controller
usa ese bool para evitar mandar email duplicado.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import boto3
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session as OrmSession

from models.message import ContactQueueMessage
from shared.aws.ssm import get_secret_by_name
from shared.db.models import Contact
from shared.db.repository import ensure_session_and_visit
from shared.db.session import db_session
from shared.observability.logger import logger

_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / 'templates'


def save_contact_idempotent(msg: ContactQueueMessage) -> dict[str, Any]:
    """UPSERT session + visit + INSERT contact con ON CONFLICT id DO NOTHING.

    Returns
    -------
    dict
        `{'persisted': bool, 'contact_id': str, 'created_at': str}`.
        `persisted=False` significa que el contact_id YA existia
        (mensaje re-entregado por SQS) — el caller NO debe mandar email.
    """
    visit_niche = msg.niche or msg.origin_niche

    with db_session() as session:
        # Paso 1: UPSERT session + visit (siempre, sin importar idempotencia
        # del contact — visits sirven para tracking analytics).
        ensure_session_and_visit(
            session,
            session_id=msg.session_id,
            ip=msg.ip,
            country=msg.country,
            user_agent=msg.user_agent,
            browser=None, browser_version=None, os_name=None, device_type=None,
            utm_source=None, utm_medium=None, utm_campaign=None,
            utm_content=None, utm_term=None,
            referrer=None, landing_page_path=None,
            niche=visit_niche,
            bump_event_count=True,
        )

        # Paso 2: INSERT contact con ON CONFLICT DO NOTHING.
        stmt = pg_insert(Contact).values(
            id=msg.contact_id,
            created_at=msg.created_at,
            name=msg.name,
            email=msg.email,
            message=msg.message,
            company=msg.company,
            role=msg.role,
            service_type=msg.service_type,
            budget=msg.budget,
            timeline=msg.timeline,
            niche=msg.niche,
            session_id=msg.session_id,
        ).on_conflict_do_nothing(index_elements=['id'])
        result = session.execute(stmt)

    # rowcount == 0 -> ya existia (no-op); == 1 -> inserto nuevo
    persisted = (result.rowcount or 0) > 0

    return {
        'persisted': persisted,
        'contact_id': msg.contact_id,
        'created_at': msg.created_at.isoformat(),
    }


def send_owner_email_safe(msg: ContactQueueMessage, persist_result: dict) -> None:
    """Envia email; si SES falla, propaga (handler marca batchItemFailure).

    A diferencia del flujo sync viejo (que silenciaba el error con un log),
    aqui el fallo del email RE-ENCOLA el mensaje. Esto es seguro porque
    save_contact_idempotent es no-op en reintentos: el contact se persiste
    UNA vez y solo el email se reintenta hasta success.

    El owner puede recibir el mismo email max 3 veces (max_receive_count)
    antes del DLQ. Es un trade-off aceptable vs perder el lead silenciosamente.
    """
    from_address = get_secret_by_name('ses-from-address', local_env='EMAIL_FROM')
    recipients_raw = get_secret_by_name('owner-email', local_env='OWNER_EMAIL')
    recipients = [r.strip() for r in recipients_raw.split(',') if r.strip()]

    html = (_TEMPLATES_DIR / 'owner_email.html').read_text(encoding='utf-8')
    text = (_TEMPLATES_DIR / 'owner_email.txt').read_text(encoding='utf-8')

    context = msg.model_dump() | persist_result
    html_body = _render_mustache_lite(html, context)
    text_body = _render_mustache_lite(text, context)

    subject = (
        f'Portfolio · Nuevo contacto de {msg.name} '
        f'({msg.niche or "generic"})'
    )

    ses = boto3.client('sesv2', region_name=os.environ.get('AWS_SES_REGION', 'us-east-1'))
    resp = ses.send_email(
        FromEmailAddress=f'The Full Stack <{from_address}>',
        Destination={'ToAddresses': recipients},
        ReplyToAddresses=[msg.email],
        Content={'Simple': {
            'Subject': {'Data': subject, 'Charset': 'UTF-8'},
            'Body': {
                'Text': {'Data': text_body, 'Charset': 'UTF-8'},
                'Html': {'Data': html_body, 'Charset': 'UTF-8'},
            },
        }},
    )
    logger.info(
        'owner email sent',
        extra={
            'message_id': resp.get('MessageId'),
            'contact_id': msg.contact_id,
            'recipient_count': len(recipients),
        },
    )


def _render_mustache_lite(template: str, context: dict[str, Any]) -> str:
    """Mismo render minimal que el contact_form (mover a shared en el futuro)."""
    # Identico al de contact_form/core/services/contact_service.py
    def conditional_replacer(match):
        var = match.group(1); block = match.group(2); value = context.get(var)
        return block.replace(f'{{{{{var}}}}}', str(value)) if value else ''

    rendered = re.sub(
        r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}',
        conditional_replacer, template, flags=re.DOTALL,
    )

    def simple_replacer(match):
        var = match.group(1); value = context.get(var, '')
        return str(value) if value else ''

    return re.sub(r'\{\{(\w+)\}\}', simple_replacer, rendered)
```

## Tests clave (formato testing standard)

Un archivo por escenario. Ver lista en "Estructura del Lambda" arriba.

### `test_process_controller_idempotent_on_conflict.py`

```python
"""
Given un mensaje SQS con contact_id que YA existe en Neon,
When Process.execute() corre,
Then `data` retorna {contact_id, skipped: True} y NO se manda email.
"""
import pytest
from controllers.worker.process import Process
from models.message import ContactQueueMessage


def test_process_skips_email_when_contact_already_persisted(
    mocker, contact_in_db, sample_message
):
    # Arrange: contact_in_db precarga el row con el mismo id
    msg = ContactQueueMessage(**sample_message(contact_id=contact_in_db.id))
    mock_send = mocker.patch('services.persistence.send_owner_email_safe')

    # Act
    controller = Process(validated_data=msg)
    result = controller.execute()

    # Assert
    assert result == {
        'is_valid': True,
        'data': {'contact_id': contact_in_db.id, 'skipped': True},
        'code': 0,
    }
    mock_send.assert_not_called()
```

### `test_handler_marks_failed_items_when_email_throws.py`

```python
"""
Given el envio de email lanza una excepcion,
When lambda_handler procesa el batch,
Then el record va en batchItemFailures con su messageId para retry SQS.
"""
import json
from unittest.mock import patch
from handler import lambda_handler


def test_email_failure_marks_batch_item_failure(sample_sqs_event):
    with patch('services.persistence.send_owner_email_safe', side_effect=Exception('SES down')):
        result = lambda_handler(sample_sqs_event, None)
    assert result == {'batchItemFailures': [{'itemIdentifier': 'msg-1'}]}
```

### `test_idempotent_on_duplicate_message_id_e2e.py` (integration)

```python
"""
Given Neon con la tabla `contacts` vacia,
When lambda_handler se invoca 2 veces con el mismo mensaje (mismo contact_id),
Then la 1ra vez persiste + manda email; la 2da vez es no-op (rowcount=0)
     y NO manda email. La tabla tiene exactamente 1 fila.
"""
# Usa Neon de test, moto SES.
```

## Reglas duras

- **SIEMPRE** el worker es idempotente. Reintentos SQS NO duplican contacts
  ni emails.
- **SIEMPRE** el handler usa `ReportBatchItemFailures` con messageId para
  permitir reintento selectivo (aunque batch=1, el formato es el mismo).
- **SIEMPRE** los errores de persistencia O email re-encolan el mensaje
  (retry SQS). Despues de max_receive_count=3 -> DLQ.
- **SIEMPRE** `contact_id`, `created_at` y `session_id` vienen del mensaje;
  el worker NO los regenera.
- **NUNCA** el worker valida Turnstile (eso ya paso en el encoder).
- **NUNCA** el worker hace rate-limit (eso ya paso en el encoder).
- **NUNCA** el worker logea el `cf_token` (no esta en el mensaje — el
  encoder NO lo incluye al encolar).
- **NUNCA** el worker procesa mensajes con `schema_version != 1` sin
  rechazo explicito (futuro: branch por version).

## AC cubiertos

- AC-9 (persiste correctamente)
- AC-10 (idempotencia)
- AC-11 (email failure -> retry)

## Verificacion incremental

```bash
serverless tests --type=unit --lambda=contact_worker
serverless tests --type=integration --lambda=contact_worker
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Worker re-valida Turnstile | Doble validacion innecesaria, fuera de tiempo | Encoder ya valido |
| Worker silencia email failure | Lead se pierde sin DLQ | Propaga -> retry SQS -> DLQ |
| Worker regenera `contact_id` | Rompe idempotencia | Usa el del mensaje |
| Compartir cliente SES via lru_cache pesado | Cold start lento | Crear en cada invocacion (es liviano) |
| Sin `model_config = extra='forbid'` | Aceptar campos no declarados es source de bugs | Forbid extra |

---

[< 04](04-shared-queue-publisher.md) | [Siguiente: 06 — tracking_worker >](06-tracking-worker.md)
