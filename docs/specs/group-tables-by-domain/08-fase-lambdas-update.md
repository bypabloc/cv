# 08 — Fase 4: Lambdas downstream

[README](README.md) | [07-fase-seeds](07-fase-seeds-update.md) |
**08-fase-lambdas** | [09-fase-provision](09-fase-provision-stage-prod.md)

## Objetivo

Actualizar los 4 Lambdas (`db`, `stream_processor`, `contact_form`,
`tracking_pixel`) y los repositorios compartidos (`shared/db/repository.py`,
`shared/db/cv_repository.py`) para usar los nombres nuevos de tablas,
columnas y enum values. Verificar con tests integration que cada
Lambda escribe/lee de las tablas correctas.

## Pre-requisitos

- Fases 1, 2, 3 completas en branch de prueba (modelos, migracion,
  seeds funcionando).
- **El mapeo de [13-mapeo-usos-modelos.md](13-mapeo-usos-modelos.md) es
  la fuente de verdad** de que archivos tocar.

## Cobertura por Lambda

### 4.1 — Lambda `db`

Toca: seed_service (Fase 3), controllers, services. Mayoria ya cubierta
en Fase 3.

Repositorios usados:

- `shared.db.cv_repository` — 107 hits (top-3 hot-spot del repo). Cada
  funcion que selecciona por tabla CV cambia nombres en queries SQL
  raw + ORM.
- `shared.db.repository` — 25 hits.

Verificar contra `13-mapeo-usos-modelos.md` seccion "shared/db/cv_repository.py"
y "shared/db/repository.py".

Tests:

```bash
serverless tests --type=unit --lambda=db
serverless tests --type=integration --lambda=db
```

### 4.2 — Lambda `stream_processor`

Toca: services que escriben a Neon desde DynamoDB Streams.

Archivos clave (segun 13-mapeo):

- `services/stream_processor/core/services/*.py` — imports de modelos
  + queries
- Cualquier referencia a `TrackingEvent`, `Contact`, `Session`,
  `SessionVisit` actualiza paths de import

Cambios principales:

```python
# antes
from shared.db.models import TrackingEvent, Contact, Session, SessionVisit

# despues
from shared.db.models.visitor import TrackingEvent, Contact, Session, SessionVisit
# (o seguir usando el shortcut from shared.db.models import ... porque
#  __init__.py raiz re-exporta todo)
```

Verificacion DB real post-test:

```bash
serverless tests --type=integration --lambda=stream_processor
# Cada integration test debe terminar con:
# psql "$DATABASE_URL" -c "SELECT count(*) FROM vis_tracking_events"
# y verificar que el count subio en 1 tras procesar el stream record
```

### 4.3 — Lambda `contact_form`

Toca: `contact_service.py` (18 hits) — persiste a DynamoDB; el stream
replica a `vis_contacts`.

Cambios:

- Imports actualizados (Contact, Session)
- Logger / mensajes que mencionen 'contacts' table — actualizar
  (cosmetico pero buena higiene)

Verificacion DB real post-test:

```bash
serverless tests --type=integration --lambda=contact_form
# El test debe:
# 1. POST a /contact con payload + Turnstile mockeado
# 2. Verificar fila en DynamoDB ContactsTable
# 3. (Tras stream simulado) verificar fila en Neon:
#    psql "$DATABASE_URL" -c "SELECT id, email, session_id FROM vis_contacts WHERE email = '<test-email>'"
```

### 4.4 — Lambda `tracking_pixel`

Toca: `tracking_service.py`.

Cambios analogos a contact_form.

Verificacion DB real post-test:

```bash
serverless tests --type=integration --lambda=tracking_pixel
# El test debe:
# 1. POST a /track con session/visit/event metadata
# 2. Verificar fila en DynamoDB TrackingTable
# 3. (Tras stream simulado) verificar:
#    psql "$DATABASE_URL" -c "SELECT visit_id, page_id, event_type_id FROM vis_tracking_events WHERE session_id = '<test-session>'"
#    psql "$DATABASE_URL" -c "SELECT session_id FROM vis_sessions WHERE session_id = '<test-session>'"
#    psql "$DATABASE_URL" -c "SELECT visit_id FROM vis_session_visits WHERE session_id = '<test-session>'"
```

### 4.5 — Lambda `cv` (si existe)

Segun el mapeo, hay `services/cv/...` con controllers que usan
`Profile`, `Experience`, etc. (~10 hits). Actualizar imports + asegurar
que las queries usan los nombres nuevos.

```bash
serverless tests --type=integration --lambda=cv
# Verificar GET /cv?operation=cv&action=profile retorna data renombrada
```

## Patron de verificacion DB real

Cada integration test de cada Lambda termina con una **query directa
a Neon** verificando que la data persistio correctamente. Patron:

```python
# tests/integration/test_X_e2e.py
import psycopg
from os import environ


def test_lambda_persists_correctly_e2e(db_branch_url, lambda_invoke):
    # 1. Arrange: input
    payload = {...}

    # 2. Act: invocar el lambda
    response = lambda_invoke(payload)

    # 3. Assert: respuesta correcta
    assert response['statusCode'] == 200

    # 4. Verificacion DB REAL (la clave del requisito del usuario)
    with psycopg.connect(db_branch_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM vis_contacts WHERE email = %s",
                (payload['email'],),
            )
            count, = cur.fetchone()
            assert count == 1  # AC-5: fila persistida en tabla renombrada
```

## Estrategia de migracion incremental por lambda

Cada lambda se actualiza en un commit separado para limitar el blast
radius:

| Commit | Lambda | Verificacion |
|---|---|---|
| 6 | `db` (controllers + repositories) | unit + integration |
| 7 | `stream_processor` | unit + integration con DB real |
| 8 | `contact_form` | unit + integration con DB real |
| 9 | `tracking_pixel` | unit + integration con DB real |
| 10 | `cv` (si aplica) | unit + integration con DB real |

Si un lambda falla aisladamente, se corrige sin bloquear los demas.

## Definition of done (Fase 4)

- [ ] Las 4 (o 5) lambdas redeployan sin errores en local
- [ ] Imports actualizados en todos los services (segun mapeo 13.md)
- [ ] `shared/db/cv_repository.py` y `shared/db/repository.py` usan
  nombres nuevos
- [ ] Integration tests por lambda incluyen verificacion DB real con
  `psycopg` directo
- [ ] `serverless tests --type=integration --lambda=<X>` verde para
  cada lambda
- [ ] `python devtools/run.py serverless lint-deps` sin errores

## Riesgos

- **Hits no detectados por grep**: el mapeo es generado por grep; si
  algun archivo usa import dinamico o reflection, queda fuera.
  Mitigacion: `python -m compileall -q serverless/lambda/` + integration
  tests reales contra Neon.
- **Plan cache de PG en queries preparadas**: si una query estaba
  prepared con el nombre viejo, el rename rompe la cache. Mitigacion:
  cada lambda re-conecta en cold start (psycopg3 + module-scope
  connection).
