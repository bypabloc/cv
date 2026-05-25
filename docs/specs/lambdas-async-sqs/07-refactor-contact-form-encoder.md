# 07 — Refactor `contact_form` (encoder + feature flag)

> Refactor de `contact_form` para ser un encoder ligero: valida, rate-limit,
> Turnstile, auto-blacklist, encola SQS y responde 202. Mantiene el flujo
> sync actual detras del flag `ASYNC_MODE=false` para rollback.

[< 06](06-tracking-worker.md) | [Siguiente: 08 — encoder tracking >](08-refactor-tracking-pixel-encoder.md)

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `services/contact_form/manifest.yaml` | + `uses.queues`; remover `secrets: [owner-email, ses-from-address]` cuando `ASYNC_MODE=true`; + env var `ASYNC_MODE` |
| `services/contact_form/core/controllers/contact/create.py` | Branch por `ASYNC_MODE`: encolar vs sync flow viejo |
| `services/contact_form/core/services/contact_service.py` | Extraer `enqueue_contact_message` nuevo + mantener `process_contact_form` viejo |
| `services/contact_form/core/models/contact.py` | + `ContactAcceptedOutput` (202 response model) |
| `services/contact_form/core/settings/config.py` | + `AppConfig.async_mode: bool` |
| `services/contact_form/pyproject.toml` | + dep `shared.queue` (internal) |
| `services/contact_form/tests/unit/test_*.py` | Tests nuevos para encoder + mantener tests sync |
| `services/contact_form/tests/integration/*.py` | Tests nuevos para encoder con moto SQS |

## Cambios en `manifest.yaml`

```yaml
name: contact-form
description: Encoder del form de contacto (valida + Turnstile + encola SQS).

runtime: python3.13
handler: core.handler.lambda_handler
memory: 256       # ← antes 512; encoder es liviano
timeout: 10       # ← antes 30; encoder responde rapido

trigger:
  type: http
  method: POST
  path: /contact

uses:
  queues:
    - { name: portfolio-contact-form-${stage}, access: producer }   # ← NUEVO
  tables:
    cache: read-write
    rate-limit-rules: read-write
    rate-limit-buckets: read-write
  secrets:
    - turnstile-secret
    - turnstile-bypass-secret
    # NOTA: owner-email y ses-from-address se MUEVEN al worker.
    # Mientras dure el feature flag, los mantenemos aqui para que el
    # flujo sync siga funcionando con ASYNC_MODE=false.
    - owner-email
    - ses-from-address
    - neon-url            # idem: solo usado en modo sync
  sends-email: true       # idem

env:
  default:
    LOG_LEVEL: INFO
    AWS_SES_REGION: us-east-1
    ASYNC_MODE: 'true'        # ← NUEVO flag (string para env var)
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
    ASYNC_MODE: 'true'           # ← se puede flipear a 'false' para rollback
    CORS_ALLOWED_ORIGINS: '...'
```

> Cuando el flag se quite (post-deprecation), eliminar de
> `uses.secrets` los `owner-email`, `ses-from-address`, `neon-url` (ya no
> los necesita el encoder) y bajar memory/timeout aun mas si aplica.

## Cambios en `controllers/contact/create.py`

```python
"""Controller contact/create — encoder o sync segun ASYNC_MODE."""

from __future__ import annotations

from datetime import UTC, datetime

from models.contact import (
    ContactAcceptedOutput,
    ContactCreatedOutput,
    ContactCreateModel,
)
from services.contact_service import (
    enqueue_contact_message,         # ← NUEVO
    process_contact_form,            # ← se mantiene para sync
)
from settings.config import AppConfig, logger
from shared.core.niches import niche_from_origin
from shared.core.ulid import new_uuidv7
from shared.http.turnstile import verify_turnstile_token
from shared.lambda_kit import BaseController
from shared.rate_limit import check_or_raise
from shared.rate_limit.auto_blacklist import (
    create_blacklist_rule,
    should_auto_blacklist,
)
from shared.rate_limit.buckets import increment_bucket


_ENDPOINT = '/contact'
_WINDOW_SECONDS = 60


def _resolve_session_id(form_session_id: str | None) -> str:
    if form_session_id:
        return form_session_id
    return f'cf-{new_uuidv7()}'


class Create(BaseController):
    event_model = ContactCreateModel

    def execute(self) -> dict:
        data: ContactCreateModel = self.validated_data
        meta = data.meta

        # 1. Rate-limit (puede levantar 429/403) — IGUAL que antes
        check_or_raise(
            ip=meta.ip, endpoint=_ENDPOINT,
            country=meta.country, turnstile_validated=False,
        )

        # 2. Turnstile (puede levantar 403) — IGUAL que antes
        verify_turnstile_token(
            data.cf_token, remote_ip=meta.ip,
            bypass_secret=meta.bypass_secret,
        )

        # 3. session_id + niche
        form_fields = data.form_fields()
        session_id = _resolve_session_id(form_fields.get('session_id'))
        origin_niche = niche_from_origin(meta.origin)
        form_fields_with_session = {**form_fields, 'session_id': session_id}

        # 4. Branch por feature flag
        if AppConfig.async_mode:
            result = self._execute_async(
                form_fields=form_fields_with_session,
                session_id=session_id,
                meta=meta,
                origin_niche=origin_niche,
            )
        else:
            result = self._execute_sync(
                form_fields=form_fields_with_session,
                session_id=session_id,
                meta=meta,
                origin_niche=origin_niche,
            )

        # 5. Auto-blacklist counter (en AMBOS modos, ANTES de retornar)
        bucket = increment_bucket(
            ip=meta.ip, endpoint=_ENDPOINT,
            window_seconds=_WINDOW_SECONDS,
            turnstile_validated=True,
        )
        if should_auto_blacklist(bucket['turnstile_tokens']):
            create_blacklist_rule(meta.ip)
            logger.warning(
                'auto-blacklisted IP',
                extra={'ip': meta.ip,
                       'turnstile_tokens': bucket['turnstile_tokens']},
            )

        return result

    def _execute_async(
        self, *, form_fields, session_id, meta, origin_niche,
    ) -> dict:
        """Modo nuevo: encola SQS y responde 202."""
        contact_id = new_uuidv7()
        created_at = datetime.now(UTC)

        enqueue_contact_message(
            contact_id=contact_id,
            created_at=created_at,
            form_fields=form_fields,
            session_id=session_id,
            ip=meta.ip,
            country=meta.country,
            user_agent=meta.user_agent,
            origin_niche=origin_niche,
        )

        output = ContactAcceptedOutput(
            contact_id=contact_id,
            created_at=created_at,
            accepted=True,
        )
        return {
            'is_valid': True,
            'data': output.model_dump(mode='json'),
            'code': 0,
        }

    def _execute_sync(
        self, *, form_fields, session_id, meta, origin_niche,
    ) -> dict:
        """Modo legacy: persiste + email sincronamente (para rollback)."""
        result = process_contact_form(
            form_fields=form_fields,
            session_id=session_id,
            ip=meta.ip,
            country=meta.country,
            user_agent=meta.user_agent,
            origin_niche=origin_niche,
        )
        output = ContactCreatedOutput(**result)
        return {
            'is_valid': True,
            'data': output.model_dump(mode='json'),
            'code': 0,
        }
```

## Cambios en `services/contact_service.py`

```python
"""@module contact_service — modo async (encolar) + modo sync legacy."""

# ... mantener todo lo actual (save_contact, send_owner_email, process_contact_form)
# ... agregar al final:

from datetime import datetime
from typing import Any

from models.message_publish import build_contact_message
from shared.queue import send_to_queue

def enqueue_contact_message(
    *,
    contact_id: str,
    created_at: datetime,
    form_fields: dict[str, Any],
    session_id: str,
    ip: str,
    country: str | None,
    user_agent: str | None,
    origin_niche: str | None,
) -> str:
    """Encola el mensaje SQS hacia contact_worker.

    Returns el MessageId (no se devuelve al cliente; solo se logea para
    correlacion con CloudWatch).
    """
    payload = build_contact_message(
        contact_id=contact_id,
        created_at=created_at,
        form_fields=form_fields,
        session_id=session_id,
        ip=ip,
        country=country,
        user_agent=user_agent,
        origin_niche=origin_niche,
    )
    return send_to_queue(
        queue_short_name='contact-form',
        payload=payload,
    )
```

> `build_contact_message` vive en un modulo nuevo `models/message_publish.py`
> y arma el dict que matchea el `ContactQueueMessage` del worker. Asi el
> encoder NO importa el modelo del worker (independencia de deploy), solo
> el dict shape. Tests garantizan compatibilidad.

## Cambios en `models/contact.py`

```python
# ... mantener ContactCreateModel y ContactCreatedOutput (sync) ...

from datetime import datetime
from pydantic import BaseModel


class ContactAcceptedOutput(BaseModel):
    """Response del encoder en modo ASYNC_MODE=true (HTTP 202)."""
    contact_id: str
    created_at: datetime
    accepted: bool = True
```

## Cambios en `settings/config.py`

```python
# ... agregar al final ...

import os

class AppConfig:
    """Config singleton del Lambda."""

    # ... existentes ...

    async_mode: bool = os.environ.get('ASYNC_MODE', 'true').lower() == 'true'
```

## Cambios en `handler.py`

Cambiar `success_status=201` por `success_status=202` SOLO cuando
`ASYNC_MODE=true`. Hay 2 opciones:

**Opcion A** (recomendada): el `http_handler` lee `AppConfig.async_mode` y
ajusta el status:

```python
return http_handler(
    event,
    event_model=_EVENT_MODEL,
    cors_origin='echo',
    success_status=202 if AppConfig.async_mode else 201,
    metric_names={...},
)
```

**Opcion B**: el controller incluye el status en su `data` y el handler lo
respeta. Mas invasivo al kit; preferir A.

## Cambios en `pyproject.toml`

```toml
[project.optional-dependencies]
# ... existente ...

[tool.shared]
internal-deps = [
  "shared.lambda_kit",
  "shared.observability",
  "shared.aws",
  "shared.rate_limit",
  "shared.http",
  "shared.core",
  "shared.cache",
  "shared.db",          # ← se mantiene mientras dure el flag (sync mode)
  "shared.queue",       # ← NUEVO
]
```

## Tests nuevos (encoder)

### `test_handler_returns_202_with_contact_id_in_async_mode.py`

```python
"""
Given ASYNC_MODE=true + form valido + Turnstile valido,
When POST /contact se invoca,
Then responde HTTP 202 con body {contact_id, accepted: true} en <800ms.
"""

import os
from unittest.mock import patch

def test_handler_returns_202_in_async_mode(monkeypatch, valid_http_event, mock_sqs):
    monkeypatch.setenv('ASYNC_MODE', 'true')
    with patch('shared.http.turnstile.verify_turnstile_token'):
        from handler import lambda_handler
        resp = lambda_handler(valid_http_event, None)

    assert resp['statusCode'] == 202
    body = json.loads(resp['body'])
    assert 'contact_id' in body
    assert body['accepted'] is True
    # Verifica que SQS recibio 1 mensaje
    assert mock_sqs.received_count == 1
```

### `test_handler_returns_201_in_sync_mode_legacy.py`

```python
"""
Given ASYNC_MODE=false (modo legacy de rollback),
When POST /contact se invoca con form valido,
Then responde HTTP 201 con body completo (igual al comportamiento viejo).
"""
```

### `test_async_mode_does_not_call_send_email.py`

```python
"""
Given ASYNC_MODE=true,
When el encoder procesa /contact,
Then send_owner_email NUNCA se invoca (el worker lo hara).
"""
```

### `test_turnstile_failure_does_not_enqueue.py`

```python
"""
Given ASYNC_MODE=true + Turnstile token invalido,
When POST /contact se invoca,
Then responde HTTP 403 Y send_to_queue NUNCA se invoca.
"""
```

### `test_rate_limit_failure_does_not_enqueue.py`

```python
"""
Given ASYNC_MODE=true + IP rate-limited,
When POST /contact se invoca,
Then responde HTTP 429 Y send_to_queue NUNCA se invoca.
"""
```

### `test_enqueue_failure_returns_500.py`

```python
"""
Given ASYNC_MODE=true + SQS down,
When POST /contact se invoca con form valido,
Then responde HTTP 502 con error explicativo (NO 201, NO 202).
"""
```

### `test_build_contact_message_matches_worker_schema.py`

```python
"""
Given los campos del request,
When build_contact_message construye el payload,
Then el dict es compatible con TrackingQueueMessage.model_validate
     (importado del worker como referencia en el test).
"""
```

### `test_auto_blacklist_runs_in_both_modes.py`

```python
"""
Given ASYNC_MODE=true Y ASYNC_MODE=false,
When un IP supera el threshold (3+ tokens validos en 60s),
Then create_blacklist_rule se invoca en AMBOS modos.
"""
```

## Tests existentes a mantener / adaptar

| Test | Accion |
|------|--------|
| `test_valid_form_creates_contact_e2e.py` | MODIFICAR: agregar parametrize sobre ASYNC_MODE |
| `test_invalid_turnstile_returns_403_e2e.py` | MANTENER (igual en ambos modos) |
| `test_rate_limit_returns_429_e2e.py` | MANTENER (igual en ambos modos) |
| `test_email_failure_still_persists_e2e.py` | RENOMBRAR: solo aplica a modo sync; nuevo test cubre el worker |

## Reglas duras

- **SIEMPRE** el flag `ASYNC_MODE` se lee UNA vez (module-scope via
  `AppConfig`) — no por invocacion.
- **SIEMPRE** Turnstile + rate-limit + auto-blacklist corren en AMBOS
  modos, ANTES del branch async/sync.
- **SIEMPRE** los UUIDv7 + timestamps se generan en el encoder (no en el
  worker), aun en modo async.
- **SIEMPRE** si `send_to_queue` falla, el handler retorna 502 — NO se
  hace fallback a sync (eso es comportamiento accidental dificil de
  debuggear).
- **NUNCA** el encoder en modo async toca Neon ni SES.
- **NUNCA** el encoder en modo async incluye `cf_token` en el mensaje SQS.
- **NUNCA** el sync mode se borra mientras el flag exista — el rollback
  depende de el.

## AC cubiertos

- AC-1 (202 async path)
- AC-2 (Turnstile invalido NO encola)
- AC-3 (rate-limit NO encola)
- AC-4 (form invalido NO encola)
- AC-5 (sync legacy mode)
- AC-18 (flag se respeta sin redeploy del worker)

## Verificacion incremental

```bash
serverless tests --type=unit --lambda=contact_form
serverless tests --type=integration --lambda=contact_form
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Branch async/sync DENTRO de service.process_contact_form | Mezcla responsabilidades | Branch en el controller |
| Leer ASYNC_MODE en cada invocacion | Penalty por invocacion warm | Module-scope (`AppConfig`) |
| Fallback automatico a sync si SQS falla | Comportamiento impredecible | Falla explicita 502 |
| Borrar el sync code "para limpiar" durante el rollout | Bloquea rollback | Solo tras 1-2 semanas de async estable |
| Generar `contact_id` en el worker | Imposible devolver al cliente | UUIDv7 en el encoder |

---

[< 06](06-tracking-worker.md) | [Siguiente: 08 — encoder tracking >](08-refactor-tracking-pixel-encoder.md)
