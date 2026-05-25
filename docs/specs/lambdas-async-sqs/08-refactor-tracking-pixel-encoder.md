# 08 — Refactor `tracking_pixel` (encoder + feature flag)

> Refactor de `tracking_pixel` para ser un encoder ligero. Mismo patron que
> contact_form pero mas simple (no Turnstile, no SES, no auto-blacklist).
> Mantiene el flujo sync detras de `ASYNC_MODE=false`.

[< 07](07-refactor-contact-form-encoder.md) | [Siguiente: 09 — idempotencia ORM >](09-idempotencia-orm.md)

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `services/tracking_pixel/manifest.yaml` | + `uses.queues`; + `ASYNC_MODE`; mantener `neon-url` mientras dure el flag |
| `services/tracking_pixel/core/controllers/tracking/track.py` | Branch por `ASYNC_MODE`: encolar vs sync flow |
| `services/tracking_pixel/core/services/tracking_service.py` | + `enqueue_tracking_message`; mantener `process_tracking_event` |
| `services/tracking_pixel/core/models/tracking.py` | + `TrackAcceptedOutput` |
| `services/tracking_pixel/core/settings/config.py` | + `AppConfig.async_mode` |
| `services/tracking_pixel/pyproject.toml` | + `shared.queue` |
| `services/tracking_pixel/tests/unit/test_*.py` | Tests del encoder |

## Cambios en `manifest.yaml`

```yaml
name: tracking-pixel
description: Encoder de eventos de tracking (valida + rate-limit + encola SQS).

runtime: python3.13
handler: core.handler.lambda_handler
memory: 128       # ← antes 256; encoder es muy liviano
timeout: 5        # ← antes 10; encoder responde rapido

trigger:
  type: http
  method: POST
  path: /track

uses:
  queues:
    - { name: portfolio-tracking-events-${stage}, access: producer }   # NUEVO
  tables:
    cache: read-write              # @cached UA parsing (mantener si ASYNC_MODE=false)
    rate-limit-rules: read-write
    rate-limit-buckets: read-write
  secrets:
    - neon-url                     # mantener mientras dure el flag

env:
  default:
    LOG_LEVEL: INFO
    ASYNC_MODE: 'true'             # NUEVO
  dev:
    LOG_LEVEL: INFO
    ASYNC_MODE: 'true'
    CORS_ALLOWED_ORIGINS: '...'
  stage:
    LOG_LEVEL: INFO
    ASYNC_MODE: 'true'
    CORS_ALLOWED_ORIGINS: '...'
  prod:
    LOG_LEVEL: WARNING
    ASYNC_MODE: 'true'
    CORS_ALLOWED_ORIGINS: '...'
```

## Cambios en `controllers/tracking/track.py`

```python
"""Controller tracking/track — encoder o sync segun ASYNC_MODE."""

from __future__ import annotations

from datetime import UTC, datetime

from models.tracking import (
    TrackAcceptedOutput,
    TrackEventModel,
)
from services.tracking_service import (
    enqueue_tracking_message,         # NUEVO
    process_tracking_event,           # mantener para sync
)
from settings.config import AppConfig, ErrorCode
from shared.core.exceptions import ApplicationError
from shared.core.ulid import new_uuidv7
from shared.lambda_kit import BaseController
from shared.rate_limit import check_or_raise


_TRACK_ENDPOINT = '/track'


class Track(BaseController):
    event_model = TrackEventModel

    def execute(self) -> dict:
        data: TrackEventModel = self.validated_data
        meta = data.meta

        # 1. Rate-limit (mantener IGUAL en ambos modos)
        try:
            check_or_raise(
                ip=meta.ip, endpoint=_TRACK_ENDPOINT,
                country=meta.country, turnstile_validated=False,
            )
        except ApplicationError as exc:
            return {
                'is_valid': False,
                'data': {
                    'error_code': exc.code,
                    'message': exc.message or exc.code,
                    'application_error': exc,
                },
                'code': ErrorCode.RATE_LIMITED.value,
            }

        # 2. Branch por feature flag
        if AppConfig.async_mode:
            return self._execute_async(data=data, meta=meta)
        return self._execute_sync(data=data, meta=meta)

    def _execute_async(self, *, data, meta) -> dict:
        """Encola SQS y responde 202."""
        page_id = new_uuidv7()
        created_at = datetime.now(UTC)

        enqueue_tracking_message(
            page_id=page_id,
            created_at=created_at,
            validated_input=data.tracking_payload(),
            ip=meta.ip,
            user_agent=meta.user_agent,
            country=meta.country,
        )

        output = TrackAcceptedOutput(
            page_id=page_id,
            session_id=data.tracking_payload()['session_id'],
            created_at=created_at,
            accepted=True,
        )
        return {
            'is_valid': True,
            'data': {
                'operation': 'tracking',
                'action': 'track',
                'status': 'accepted',
                **output.model_dump(mode='json'),
            },
            'code': 0,
        }

    def _execute_sync(self, *, data, meta) -> dict:
        """Modo legacy: persiste sincronamente."""
        result = process_tracking_event(
            validated_input=data.tracking_payload(),
            ip=meta.ip,
            user_agent=meta.user_agent,
            country=meta.country,
        )
        return {
            'is_valid': True,
            'data': {
                'operation': 'tracking', 'action': 'track', 'status': 'ok',
                **result,
            },
            'code': 0,
        }
```

## Cambios en `services/tracking_service.py`

```python
# ... mantener parse_user_agent, save_tracking_event, process_tracking_event ...
# ... agregar al final ...

from datetime import datetime
from typing import Any

from shared.queue import send_to_queue


def enqueue_tracking_message(
    *,
    page_id: str,
    created_at: datetime,
    validated_input: dict[str, Any],
    ip: str,
    user_agent: str | None,
    country: str | None = None,
) -> str:
    """Encola el mensaje SQS hacia tracking_worker.

    NOTA: el encoder NO hace UA parsing — el worker lo hace (cacheado).
    Asi el encoder es minimo y responde rapido.
    """
    payload = {
        'schema_version': 1,
        'page_id': page_id,
        'created_at': created_at.isoformat(),
        'session_id': validated_input['session_id'],
        'event_id': validated_input['event_id'],
        'event_type_id': validated_input['event_type_id'],
        'page_path': validated_input.get('page_path'),
        'niche': validated_input.get('niche'),
        'viewport_width': validated_input['viewport_width'],
        'viewport_height': validated_input['viewport_height'],
        'event_props': validated_input.get('event_props'),
        'utm_source': validated_input.get('utm_source'),
        'utm_medium': validated_input.get('utm_medium'),
        'utm_campaign': validated_input.get('utm_campaign'),
        'utm_content': validated_input.get('utm_content'),
        'utm_term': validated_input.get('utm_term'),
        'referrer': validated_input.get('referrer'),
        'ip': ip,
        'country': country,
        'user_agent': user_agent,
    }
    return send_to_queue(
        queue_short_name='tracking-events',
        payload=payload,
    )
```

## Cambios en `models/tracking.py`

```python
# ... mantener TrackEventModel ...

from datetime import datetime
from pydantic import BaseModel


class TrackAcceptedOutput(BaseModel):
    """Response del encoder en modo ASYNC_MODE=true."""
    page_id: str
    session_id: str
    created_at: datetime
    accepted: bool = True
```

## Cambios en `settings/config.py`

```python
# ... agregar al final ...

import os

class AppConfig:
    # ... existentes ...
    async_mode: bool = os.environ.get('ASYNC_MODE', 'true').lower() == 'true'
```

## Cambios en `handler.py`

```python
return http_handler(
    event,
    event_model=_EVENT_MODEL,
    cors_origin='public',
    success_status=202 if AppConfig.async_mode else 204,   # ← 202 vs 204
    metric_names={
        'submitted': 'TrackingEventReceived',
        'rejected': 'TrackingEventRejected',
        'error': 'TrackingEventError',
    },
)
```

## Cambios en `pyproject.toml`

```toml
[tool.shared]
internal-deps = [
  "shared.lambda_kit",
  "shared.observability",
  "shared.aws",
  "shared.rate_limit",
  "shared.http",
  "shared.core",
  "shared.cache",
  "shared.db",          # mantener mientras dure el flag
  "shared.queue",       # NUEVO
]
```

## Tests nuevos del encoder

### `test_handler_returns_202_with_page_id_in_async_mode.py`

```python
"""
Given ASYNC_MODE=true + body /track valido,
When lambda_handler procesa,
Then responde HTTP 202 con body que incluye page_id + session_id + accepted.
"""
```

### `test_handler_returns_204_in_sync_mode_legacy.py`

```python
"""
Given ASYNC_MODE=false,
When /track valido,
Then comportamiento identico al actual (HTTP 204, escribe a Neon).
"""
```

### `test_async_mode_does_not_call_neon.py`

```python
"""
Given ASYNC_MODE=true,
When el encoder procesa,
Then ninguna funcion del shared.db.session se invoca (verificado con patch
     sobre db_session).
"""
```

### `test_rate_limit_failure_does_not_enqueue.py`

```python
"""
Given ASYNC_MODE=true + IP rate-limited,
When POST /track,
Then responde con code RATE_LIMITED Y send_to_queue NUNCA se invoca.
"""
```

### `test_enqueue_failure_returns_error.py`

```python
"""
Given ASYNC_MODE=true + SQS down,
When POST /track,
Then responde HTTP 502 con error explicativo.
"""
```

### `test_encoder_does_not_parse_user_agent.py`

```python
"""
Given ASYNC_MODE=true,
When encoder procesa,
Then parse_user_agent NUNCA se invoca (eso es del worker).
"""
```

### `test_message_payload_is_serializable_json.py`

```python
"""
Given un evento /track valido con datetime + UUIDs,
When build del payload del mensaje,
Then json.dumps(payload, default=str) no lanza excepcion Y
     deserializa de vuelta al mismo dict.
"""
```

## Tests existentes a mantener / adaptar

| Test | Accion |
|------|--------|
| `test_valid_event_persists_e2e.py` | RENOMBRAR a `..._sync_mode` y parametrizar con ASYNC_MODE=false |
| `test_rate_limit_exceeded_e2e.py` | MANTENER (igual en ambos modos) |
| `test_user_agent_*` | MANTENER pero MOVER al worker (ahora UA parsing es del worker) |
| `test_event_props_persisted_e2e.py` | RENOMBRAR a `..._sync` y crear espejo en worker integration |

## Reglas duras

- **SIEMPRE** el encoder en modo async NO parsea UA (carga 5-10ms; lo hace
  el worker, donde es OK pagar el costo).
- **SIEMPRE** `ASYNC_MODE` se lee module-scope.
- **SIEMPRE** `page_id` y `created_at` en el encoder (el worker NO los
  regenera).
- **SIEMPRE** `session_id` se conserva tal como viene del cliente (es del
  navegador).
- **NUNCA** el encoder en modo async toca Neon.
- **NUNCA** el encoder en modo async escribe al cache de UA (es lectura
  unica del worker; el cache es compartido para que el worker reuse
  parses previos del encoder en modo legacy).

## AC cubiertos

- AC-6 (202 async path)
- AC-7 (rate-limit NO encola)
- AC-8 (form invalido NO encola)
- AC-18 (flag se respeta sin redeploy del worker)

## Verificacion incremental

```bash
serverless tests --type=unit --lambda=tracking_pixel
serverless tests --type=integration --lambda=tracking_pixel
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| UA parsing en el encoder | Latencia extra fuera de necesidad | UA solo en el worker |
| `page_id` generado en el worker | Idempotencia rota | Encoder lo genera |
| `created_at` = `datetime.now()` en el worker | Time skew si SQS demora | Encoder lo fija |
| Fallback automatico a sync ante SQS fail | Bug oculto | 502 explicito |
| `time.sleep` en el encoder esperando SQS | Anula la mejora | Sin sleeps |

---

[< 07](07-refactor-contact-form-encoder.md) | [Siguiente: 09 — idempotencia ORM >](09-idempotencia-orm.md)
