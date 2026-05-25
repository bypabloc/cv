# 06 — Worker `tracking_worker` (SQS batch=10 -> Neon)

> Nuevo Lambda `tracking_worker` que consume la cola SQS
> `portfolio-tracking-events-${stage}` con batch_size=10, parsea UA
> (cacheado), y escribe a Neon compartiendo UNA conexion para todo el
> batch. Maneja fallos parciales con `ReportBatchItemFailures`.

[< 05](05-contact-worker.md) | [Siguiente: 07 — encoder contact >](07-refactor-contact-form-encoder.md)

---

## Estructura del Lambda

```text
serverless/lambda/services/tracking_worker/
├── manifest.yaml
├── pyproject.toml
├── .gitignore
├── uv.lock
├── core/
│   ├── __init__.py
│   ├── handler.py                       # SQS batch event router
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── worker/
│   │       ├── __init__.py
│   │       └── process_batch.py         # operation=worker, action=process_batch
│   ├── services/
│   │   ├── __init__.py
│   │   └── persistence.py               # save_tracking_event_idempotent (batch)
│   ├── models/
│   │   ├── __init__.py
│   │   └── message.py                   # TrackingQueueMessage
│   └── settings/
│       ├── __init__.py
│       ├── config.py
│       └── operations.py
├── events/
│   ├── sample_batch.json                # 10 records SQS
│   └── sample_single.json
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── integration/
    │   ├── __init__.py
    │   ├── conftest.py
    │   ├── _fixtures/
    │   ├── test_batch_persists_all_events_one_connection_e2e.py
    │   ├── test_partial_failure_returns_batch_item_failures_e2e.py
    │   └── test_duplicate_message_no_ops_e2e.py
    └── unit/
        ├── __init__.py
        ├── _helpers.py
        ├── test_handler_processes_full_batch_no_failures.py
        ├── test_handler_marks_individual_failures_with_id.py
        ├── test_handler_continues_after_single_item_exception.py
        ├── test_message_model_accepts_valid_event.py
        ├── test_message_model_rejects_missing_session_id.py
        ├── test_process_batch_controller_shares_db_session.py
        └── test_process_batch_controller_idempotent_on_conflict.py
```

## `manifest.yaml`

```yaml
name: tracking-worker
description: Procesa batches SQS de tracking events (Neon, batch=10).

runtime: python3.13
handler: core.handler.lambda_handler
memory: 256       # MB — un batch de 10 events es liviano
timeout: 10       # segundos — visibility_timeout=60 = 6x

trigger:
  type: sqs
  queue: portfolio-tracking-events-${stage}
  batch_size: 10
  function_response_types:
    - ReportBatchItemFailures

uses:
  queues:
    - { name: portfolio-tracking-events-${stage}, access: consumer }
  tables:
    cache: read-write           # @cached UA parsing
  secrets:
    - neon-url
  sends-email: false

env:
  default:
    LOG_LEVEL: INFO
  dev:
    LOG_LEVEL: INFO
  stage:
    LOG_LEVEL: INFO
  prod:
    LOG_LEVEL: WARNING
```

## `core/handler.py`

```python
"""Lambda tracking_worker — consume SQS portfolio-tracking-events-${stage}.

Procesa batches de hasta 10 mensajes. CADA mensaje se procesa por
separado pero comparten la MISMA conexion Neon (cold-start de Neon
amortizado entre los 10 events). Si un mensaje falla, se devuelve en
`batchItemFailures` con su messageId — SQS borra los exitosos y
reintenta solo los fallidos.
"""

from __future__ import annotations

import json
import os
import sys

_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from typing import Any

from controllers.worker.process_batch import ProcessBatch
from settings.operations import OPERATIONS
from shared.lambda_kit import build_event_model
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
    """Procesa un batch SQS (hasta 10 records). Devuelve batchItemFailures.

    Decision: NO usamos `run_controller` por mensaje individual aqui
    porque queremos compartir la sesion Neon entre los 10. El controller
    `ProcessBatch` recibe la lista completa de records ya parseados y
    devuelve la lista de failures.
    """
    records = event.get('Records', [])
    parsed: list[dict[str, Any]] = []
    parse_failures: list[dict[str, str]] = []

    for record in records:
        try:
            body = json.loads(record['body'])
            parsed.append({'message_id': record['messageId'], 'body': body})
        except json.JSONDecodeError:
            logger.exception(
                'malformed JSON in SQS message',
                extra={'message_id': record['messageId']},
            )
            metrics.add_metric(name='TrackingMalformed', unit=MetricUnit.Count, value=1)
            parse_failures.append({'itemIdentifier': record['messageId']})

    # Delega TODA la persistencia al controller (1 conexion Neon compartida).
    controller = ProcessBatch(validated_data=parsed)
    result = controller.execute()
    failures = parse_failures + result['data'].get('failures', [])

    metrics.add_metric(
        name='TrackingProcessed',
        unit=MetricUnit.Count,
        value=len(records) - len(failures),
    )
    if failures:
        metrics.add_metric(
            name='TrackingFailed', unit=MetricUnit.Count, value=len(failures),
        )

    return {'batchItemFailures': failures}


_ = OPERATIONS
```

> El controller aqui se invoca DIRECTO (no via `run_controller`) porque
> el "payload" del controller es la lista completa de mensajes del batch,
> no un evento individual. Es una excepcion deliberada al patron
> estandar lambda-controller — documentar en el comentario del handler.

## `core/models/message.py`

```python
"""@module message — schema del mensaje SQS del tracking_worker."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Literal


class TrackingQueueMessage(BaseModel):
    """Mensaje SQS encolado por tracking_pixel encoder."""
    model_config = ConfigDict(extra='forbid')

    schema_version: Literal[1] = 1

    # IDs pre-generados por el encoder
    page_id: str                         # UUIDv7
    created_at: datetime

    # Campos validados del evento
    session_id: str
    event_id: str
    event_type_id: str
    page_path: str
    niche: str | None = None
    viewport_width: int
    viewport_height: int
    event_props: dict[str, Any] | None = None

    # UTM
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    utm_term: str | None = None
    referrer: str | None = None

    # Metadata del request HTTP
    ip: str
    country: str | None = None
    user_agent: str | None = None
```

## `core/controllers/worker/process_batch.py`

```python
"""Controller worker/process_batch — procesa hasta 10 mensajes con 1 conexion Neon.

Recibe `validated_data: list[{message_id, body}]`. Itera cada mensaje,
hace ensure_session_and_visit + INSERT tracking_event con
`ON CONFLICT DO NOTHING`. Si UNO falla, lo agrega a `failures` y sigue
con el resto. Toda la transaccion comparte la misma db_session.
"""

from __future__ import annotations

from typing import Any

from models.message import TrackingQueueMessage
from services.persistence import process_tracking_message
from shared.db.session import db_session
from shared.lambda_kit import BaseController
from shared.observability.logger import logger


class ProcessBatch(BaseController):
    """action = 'process_batch'. Procesa el batch entero compartiendo session."""

    def execute(self) -> dict:
        records: list[dict[str, Any]] = self.validated_data
        failures: list[dict[str, str]] = []

        # 1 sola conexion Neon para todos los mensajes del batch
        with db_session() as session:
            for record in records:
                msg_id = record['message_id']
                try:
                    msg = TrackingQueueMessage(**record['body'])
                    process_tracking_message(session, msg)
                except Exception:
                    logger.exception(
                        'failed to process tracking message',
                        extra={'message_id': msg_id},
                    )
                    failures.append({'itemIdentifier': msg_id})
                    # NO re-raise: continuamos con el resto del batch.
                    # NO rollback aqui: cada mensaje tiene su savepoint
                    # implicito (los INSERTS fallidos no contaminan los
                    # exitosos porque on_conflict_do_nothing nunca lanza).
                    # Si lanza otra cosa (FK violation, conexion perdida),
                    # SQLAlchemy auto-rollback al salir del with.

        return {
            'is_valid': True,
            'data': {'failures': failures, 'processed': len(records) - len(failures)},
            'code': 0,
        }
```

> **Importante sobre rollbacks**: si un INSERT falla por FK violation, la
> tx queda en estado abortado y los siguientes INSERTS del batch fallarian
> en cascada con `InFailedTransactionError`. Para evitarlo, usar savepoints
> Postgres alrededor de cada mensaje:
>
> ```python
> with session.begin_nested():  # savepoint
>     process_tracking_message(session, msg)
> ```
>
> Esto permite que un mensaje falle sin abortar la tx exterior. Ver
> implementacion completa en la fase 06 final.

## `core/services/persistence.py`

```python
"""@module persistence — INSERT idempotente de un tracking_event.

`process_tracking_message` recibe la session SQLAlchemy compartida del
batch y un mensaje validado. Hace ensure_session_and_visit + INSERT
con ON CONFLICT (created_at, visit_id, page_id) DO NOTHING.

Usa savepoint Postgres (`begin_nested`) para aislar el commit/rollback
de ESTE mensaje sin afectar al resto del batch.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session as OrmSession

from models.message import TrackingQueueMessage
from shared.cache import cached
from shared.db.models import TrackingEvent
from shared.db.repository import ensure_session_and_visit
from shared.observability.logger import logger
from ua_parser import user_agent_parser

_UA_CACHE_TTL_SECONDS = 24 * 60 * 60


@cached(ttl=_UA_CACHE_TTL_SECONDS, namespace='ua', tags=['user-agent'])
def parse_user_agent(user_agent: str | None) -> dict[str, str]:
    """Misma logica que tracking_pixel/services/tracking_service.parse_user_agent.

    Cacheada en DynamoDB; el cache es compartido entre encoder + worker
    porque usan el mismo namespace + tags.
    """
    # Implementacion identica al actual; se copia/refactoriza al porting.
    ...


def process_tracking_message(session: OrmSession, msg: TrackingQueueMessage) -> None:
    """Persiste 1 tracking_event dentro de un savepoint.

    El savepoint permite que este mensaje falle sin abortar el resto del
    batch (la tx exterior sigue viva).

    Idempotencia: si el PK (created_at, visit_id, page_id) ya existe,
    el INSERT es no-op. visit_id lo resuelve ensure_session_and_visit
    (UPSERT) — el mismo mensaje re-entregado obtiene el MISMO visit_id
    porque las 6 keys del visit-trigger coinciden.
    """
    with session.begin_nested():
        ua_info = parse_user_agent(msg.user_agent)

        # 1. UPSERT session + visit (idempotente)
        session_id, visit_id = ensure_session_and_visit(
            session,
            session_id=msg.session_id,
            ip=msg.ip,
            country=msg.country,
            user_agent=msg.user_agent,
            browser=ua_info['browser'],
            browser_version=ua_info['browser_version'],
            os_name=ua_info['os'],
            device_type=ua_info['device_type'],
            utm_source=msg.utm_source,
            utm_medium=msg.utm_medium,
            utm_campaign=msg.utm_campaign,
            utm_content=msg.utm_content,
            utm_term=msg.utm_term,
            referrer=msg.referrer,
            landing_page_path=msg.page_path,
            niche=msg.niche,
            bump_event_count=True,
        )

        # 2. INSERT tracking_event con ON CONFLICT DO NOTHING
        stmt = pg_insert(TrackingEvent).values(
            session_id=session_id,
            visit_id=visit_id,
            page_id=msg.page_id,
            created_at=msg.created_at,
            event_id=msg.event_id,
            event_type_id=msg.event_type_id,
            page_path=msg.page_path,
            niche=msg.niche,
            viewport_width=msg.viewport_width,
            viewport_height=msg.viewport_height,
            event_props=msg.event_props,
        ).on_conflict_do_nothing(
            index_elements=['created_at', 'visit_id', 'page_id']
        )
        session.execute(stmt)

    logger.debug(
        'tracking event persisted',
        extra={'page_id': msg.page_id, 'session_id': msg.session_id},
    )
```

## Tests clave

### `test_handler_continues_after_single_item_exception.py`

```python
"""
Given un batch SQS de 3 records, el segundo causa una excepcion en persistence,
When lambda_handler procesa,
Then los records 1 y 3 procesan; el 2 va en batchItemFailures.
"""
```

### `test_batch_persists_all_events_one_connection_e2e.py` (integration)

```python
"""
Given Neon de test + batch SQS con 10 events validos,
When lambda_handler corre,
Then los 10 events estan en tracking_events Y se reutilizo UNA sola
     conexion Neon (verificado con un spy sobre create_engine).
"""
```

### `test_duplicate_message_no_ops_e2e.py` (integration)

```python
"""
Given Neon con 1 tracking_event ya insertado,
When lambda_handler procesa un mensaje con el MISMO (created_at, visit_id, page_id),
Then no se inserta una segunda fila y rowcount es 0.
"""
```

### `test_process_batch_controller_shares_db_session.py`

```python
"""
Given un batch de 5 mensajes,
When ProcessBatch.execute corre,
Then `db_session()` se invoca exactamente UNA vez (no 5).
"""
```

## Reglas duras

- **SIEMPRE** una sola `db_session()` por batch (cold-start de Neon
  amortizado).
- **SIEMPRE** cada mensaje del batch va en un savepoint
  (`session.begin_nested()`) — un fallo NO contamina a los demas.
- **SIEMPRE** parseo de UA cacheado (`@cached`). El cache es compartido
  con el tracking_pixel viejo (mismo namespace `ua`).
- **SIEMPRE** Pydantic con `extra='forbid'`.
- **SIEMPRE** el handler retorna `batchItemFailures` con `itemIdentifier =
  messageId` original — NUNCA con otro id.
- **NUNCA** procesar el batch sin `begin_nested` (FK violations en 1 row
  abortan TODA la tx -> el batch entero falla).
- **NUNCA** logear `event_props` completos (pueden ser grandes y opacos).
- **NUNCA** el worker hace rate-limit ni bot detection.

## AC cubiertos

- AC-12 (batch + conexion compartida)
- AC-13 (partial failure -> batchItemFailures con messageId)
- AC-14 (idempotencia ON CONFLICT)

## Verificacion incremental

```bash
serverless tests --type=unit --lambda=tracking_worker
serverless tests --type=integration --lambda=tracking_worker
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| 1 db_session por mensaje del batch | Cold-start x10 | 1 sesion compartida |
| Sin savepoint | Un FK fail aborta los 10 | `session.begin_nested()` por mensaje |
| Rollback completo en cualquier excepcion | Se pierden los exitosos | rollback solo del savepoint |
| Re-parsear UA en cada mensaje sin cache | DynamoDB ya esta para esto | `@cached` decorator |
| Re-encolar todo el batch en falla parcial | SQS duplica los exitosos | Reportar solo los fallidos |
| `batch_size > 10` con `function_response_types` mal usado | Max 10 segun limite del integration | 10 fijo |

---

[< 05](05-contact-worker.md) | [Siguiente: 07 — encoder contact >](07-refactor-contact-form-encoder.md)
