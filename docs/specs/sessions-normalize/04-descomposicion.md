# 04 — Descomposicion en tareas atomicas

[← Archivos afectados](03-archivos-afectados.md) | [Siguiente: Commits →](05-commits.md)

Tareas atomicas con los 6 campos obligatorios. Cada tarea pasa los 3
checks: **File Exclusivity** (no toca archivos de otra tarea
concurrente), **Interface Stability** (la firma publica que expone se
acuerda antes), **Bounded Scope** (cambia una sola cosa, revisable en
<10 min).

## Tarea T1 — Migration Alembic + modelos ORM nuevos/modificados

- **Archivos**:
  - `serverless/lambda/shared/db/alembic/versions/d4e5f6a7b8c9_introduce_sessions_visits.py`
  - `serverless/lambda/shared/db/models/session.py`
  - `serverless/lambda/shared/db/models/session_visit.py`
  - `serverless/lambda/shared/db/models/tracking.py`
  - `serverless/lambda/shared/db/models/contact.py`
  - `serverless/lambda/shared/db/models/__init__.py`
- **AC referenciados**: AC-8, AC-9, AC-10, AC-11.
- **Depende de**: spec aprobada.
- **Paralelizable con**: ninguna (es la base).
- **Verify**:
  - `python -m compileall -q serverless/lambda/shared/db/models/`
  - `python -c "from shared.db.models import Session, SessionVisit, TrackingEvent, Contact"`
  - En un branch Neon de prueba: `alembic upgrade head` -> `alembic downgrade -1` -> `alembic upgrade head` (probar la migration en ambos sentidos).
- **Done**: migration corre clean up/down y los 4 modelos importan sin error.

## Tarea T2 — Repository helper `ensure_session_and_visit`

- **Archivos**:
  - `serverless/lambda/shared/db/repository.py`
  - `serverless/lambda/shared/db/__init__.py`
- **AC referenciados**: AC-1, AC-2, AC-3, AC-4.
- **Depende de**: T1 (necesita los modelos importables).
- **Paralelizable con**: T4 (modulo `niche_from_origin`) si los firma
  acordamos antes.
- **Verify**:
  - `python -m compileall -q serverless/lambda/shared/db/repository.py`
  - Unit tests del helper (con db en memoria o testcontainers PG): AC-1, AC-2, AC-3, AC-4 cubiertos.
- **Done**: el helper funciona en tests con la API descrita en [01-contexto-y-decisiones.md](01-contexto-y-decisiones.md#logica-del-backend-ensure_session_and_visit).

## Tarea T3 — `tracking_pixel`: integrar helper

- **Archivos**:
  - `serverless/lambda/services/tracking_pixel/core/services/tracking_service.py`
  - `serverless/lambda/services/tracking_pixel/core/controllers/tracking/track.py`
  - `serverless/lambda/services/tracking_pixel/tests/unit/test_save_tracking_event_persists_item.py` (modificar)
  - `serverless/lambda/services/tracking_pixel/tests/unit/test_session_upsert_idempotent.py` (nuevo)
  - `serverless/lambda/services/tracking_pixel/tests/unit/test_visit_creates_on_ip_change.py` (nuevo)
  - `serverless/lambda/services/tracking_pixel/tests/unit/test_visit_creates_on_utm_change.py` (nuevo)
  - `serverless/lambda/services/tracking_pixel/tests/integration/test_valid_event_persists_e2e.py` (modificar)
- **AC referenciados**: AC-1, AC-2, AC-3, AC-4, AC-5, AC-12.
- **Depende de**: T1, T2.
- **Paralelizable con**: T4 (archivos disjuntos).
- **Verify**:
  - `serverless tests --type=unit --lambda=tracking_pixel` -> verde.
  - `serverless tests --type=integration --lambda=tracking_pixel` -> verde.
- **Done**: la suite unit + integration de tracking_pixel pasa con los
  nuevos casos.

## Tarea T4 — `contact_form`: integrar helper + niche fallback

- **Archivos**:
  - `serverless/lambda/shared/http/niche.py` (NUEVO)
  - `serverless/lambda/services/contact_form/core/services/contact_service.py`
  - `serverless/lambda/services/contact_form/core/controllers/contact/create.py`
  - `serverless/lambda/services/contact_form/tests/unit/test_contact_creates_session_on_the_fly.py` (nuevo)
  - `serverless/lambda/services/contact_form/tests/unit/test_contact_reuses_existing_session.py` (nuevo)
  - `serverless/lambda/services/contact_form/tests/integration/test_contact_persists_e2e.py` (modificar o crear)
- **AC referenciados**: AC-6, AC-7, AC-9, AC-12.
- **Depende de**: T1, T2.
- **Paralelizable con**: T3 (archivos disjuntos).
- **Verify**:
  - `serverless tests --type=unit --lambda=contact_form` -> verde.
  - `serverless tests --type=integration --lambda=contact_form` -> verde.
- **Done**: la suite unit + integration de contact_form pasa con los
  nuevos casos. Edge case: contact sin track previo crea session
  on-the-fly con niche del Origin (AC-6).

## Tarea T5 — Verificacion E2E + deploy dev (ver [07](07-verificacion-e2e.md))

- **Archivos**: ninguno editable; ejecucion de bateria de comandos.
- **AC referenciados**: TODOS (verificacion integral).
- **Depende de**: T1, T2, T3, T4.
- **Paralelizable con**: ninguna (es la fase final).
- **Verify**: ver [07-verificacion-e2e.md](07-verificacion-e2e.md).
- **Done**: bateria completa de comandos pasa en verde + ningun
  `NotNullViolation` ni `ForeignKeyViolation` post-deploy en CloudWatch.

## Total de tareas

5 tareas. Ningun grafo de dependencias mas complejo que:

```
T1 ──► T2 ──► T3 ─┐
              │   ├─► T5
              └─► T4 ┘
```

Granularidad: medium (5 tareas). Adecuada para 1-2 devs en paralelo
(T3 + T4) tras la base.

[← Archivos afectados](03-archivos-afectados.md) | [Siguiente: Commits →](05-commits.md)
