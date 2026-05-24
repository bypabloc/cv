# 04 — Descomposicion en tareas atomicas

[← Archivos afectados](03-archivos-afectados.md) | [Siguiente: Commits →](05-commits.md)

Tareas atomicas con los 6 campos obligatorios. Cada tarea pasa los 3
checks: **File Exclusivity** (no toca archivos de otra tarea
concurrente), **Interface Stability** (la firma publica que expone se
acuerda antes), **Bounded Scope** (cambia una sola cosa, revisable en
<10 min).

## Tarea T1 — Centralizar niches en `shared/core/niches.py`

- **Archivos**:
  - `serverless/lambda/shared/core/niches.py` (NUEVO)
  - `serverless/lambda/shared/core/__init__.py`
  - `serverless/lambda/services/cv/core/models/cv.py` (elimina
    `_VALID_NICHES` local, importa `CV_NICHES`)
  - `serverless/lambda/shared/tests/unit/core/test_niches.py` (NUEVO)
- **AC referenciados**: AC-13, AC-14.
- **Depende de**: spec aprobada.
- **Paralelizable con**: T2 (migration). Archivos disjuntos
  (`shared/core/` vs `shared/db/`).
- **Verify**:
  - `python -c "from shared.core.niches import ALL_NICHES, CV_NICHES, niche_from_origin"`
  - `python -m pytest serverless/lambda/shared/tests/unit/core/test_niches.py -v` -> verde.
  - `serverless tests --type=unit --lambda=cv --aws-profile=tfs-dev` -> verde (refactor del Lambda `cv` no rompe nada).
  - `rg -n "_VALID_NICHES" serverless/lambda/` -> 0 lineas (toda la
    duplicacion eliminada).
- **Done**: el modulo existe, los tests pasan, el Lambda `cv` usa la
  fuente centralizada.

## Tarea T2 — Migration Alembic + modelos ORM nuevos/modificados

- **Archivos**:
  - `serverless/lambda/shared/db/alembic/versions/d4e5f6a7b8c9_introduce_sessions_visits.py`
  - `serverless/lambda/shared/db/models/session.py`
  - `serverless/lambda/shared/db/models/session_visit.py`
  - `serverless/lambda/shared/db/models/tracking.py`
  - `serverless/lambda/shared/db/models/contact.py`
  - `serverless/lambda/shared/db/models/__init__.py`
- **AC referenciados**: AC-8, AC-9, AC-10, AC-11.
- **Depende de**: spec aprobada. NO depende de T1 (archivos
  disjuntos).
- **Paralelizable con**: T1 (archivos disjuntos). Pero T3, T4 y T5
  dependen de T2 -> en la practica conviene secuenciar T1 -> T2 para
  reducir riesgo de conflicto en `__init__.py` de `shared/`.
- **Verify**:
  - `python -m compileall -q serverless/lambda/shared/db/models/`
  - `python -c "from shared.db.models import Session, SessionVisit, TrackingEvent, Contact"`
  - En un branch Neon de prueba: `alembic upgrade head` -> `alembic downgrade -1` -> `alembic upgrade head` (probar la migration en ambos sentidos).
  - `psql ... -c "\d+ session_visits"` muestra `event_count` con
    `default 0` y `NOT NULL`.
- **Done**: migration corre clean up/down y los 4 modelos importan sin error.

## Tarea T3 — Repository helper `ensure_session_and_visit`

- **Archivos**:
  - `serverless/lambda/shared/db/repository.py`
  - `serverless/lambda/shared/db/__init__.py`
- **AC referenciados**: AC-1, AC-2, AC-3, AC-4, AC-15.
- **Depende de**: T2 (necesita los modelos importables).
- **Paralelizable con**: ninguna en esta fase. T4 y T5 importan este
  helper, asi que necesitan su Interface Stability.
- **Verify**:
  - `python -m compileall -q serverless/lambda/shared/db/repository.py`
  - Unit tests del helper (con db en memoria o testcontainers PG):
    AC-1, AC-2, AC-3, AC-4 cubiertos. El test de AC-15 verifica que
    `event_count` se incrementa exactamente 1 por invocacion con
    `bump_event_count=True`.
- **Done**: el helper funciona en tests con la API descrita en
  [01-contexto-y-decisiones.md](01-contexto-y-decisiones.md#logica-del-backend-ensure_session_and_visit).

## Tarea T4 — `tracking_pixel`: integrar helper

- **Archivos**:
  - `serverless/lambda/services/tracking_pixel/core/services/tracking_service.py`
  - `serverless/lambda/services/tracking_pixel/core/controllers/tracking/track.py`
  - `serverless/lambda/services/tracking_pixel/tests/unit/test_save_tracking_event_persists_item.py` (modificar)
  - `serverless/lambda/services/tracking_pixel/tests/unit/test_session_upsert_idempotent.py` (nuevo)
  - `serverless/lambda/services/tracking_pixel/tests/unit/test_visit_creates_on_ip_change.py` (nuevo)
  - `serverless/lambda/services/tracking_pixel/tests/unit/test_visit_creates_on_utm_change.py` (nuevo, table-driven para 5 UTM)
  - `serverless/lambda/services/tracking_pixel/tests/unit/test_event_count_matches_count_invariant.py` (nuevo)
  - `serverless/lambda/services/tracking_pixel/tests/integration/test_valid_event_persists_e2e.py` (modificar)
- **AC referenciados**: AC-1, AC-2, AC-3, AC-4, AC-5, AC-12, AC-15,
  AC-16.
- **Depende de**: T2, T3.
- **Paralelizable con**: T5 (archivos disjuntos).
- **Verify**:
  - `serverless tests --type=unit --lambda=tracking_pixel` -> verde.
  - `serverless tests --type=integration --lambda=tracking_pixel` -> verde.
- **Done**: la suite unit + integration de tracking_pixel pasa con los
  nuevos casos.

## Tarea T5 — `contact_form`: integrar helper + niche fallback

- **Archivos**:
  - `serverless/lambda/services/contact_form/core/services/contact_service.py`
  - `serverless/lambda/services/contact_form/core/controllers/contact/create.py`
  - `serverless/lambda/services/contact_form/tests/unit/test_contact_creates_session_on_the_fly.py` (nuevo)
  - `serverless/lambda/services/contact_form/tests/unit/test_contact_reuses_existing_session.py` (nuevo)
  - `serverless/lambda/services/contact_form/tests/integration/test_contact_persists_e2e.py` (modificar o crear)
- **AC referenciados**: AC-6, AC-7, AC-9, AC-12.
- **Depende de**: T1 (importa `niche_from_origin`), T2, T3.
- **Paralelizable con**: T4 (archivos disjuntos).
- **Verify**:
  - `serverless tests --type=unit --lambda=contact_form` -> verde.
  - `serverless tests --type=integration --lambda=contact_form` -> verde.
- **Done**: la suite unit + integration de contact_form pasa con los
  nuevos casos. Edge case: contact sin track previo crea session
  on-the-fly con niche del Origin (AC-6).

## Tarea T6 — Verificacion E2E + deploy dev (ver [07](07-verificacion-e2e.md))

- **Archivos**: ninguno editable; ejecucion de bateria de comandos.
- **AC referenciados**: TODOS (verificacion integral). En especial
  AC-16 (invariante `event_count == COUNT(*)`).
- **Depende de**: T1, T2, T3, T4, T5.
- **Paralelizable con**: ninguna (es la fase final).
- **Verify**: ver [07-verificacion-e2e.md](07-verificacion-e2e.md).
- **Done**: bateria completa de comandos pasa en verde, sin ningun
  `NotNullViolation` ni `ForeignKeyViolation` post-deploy en
  CloudWatch, y con `event_count` coherente con `COUNT(*)` para todos
  los visits de prueba.

## Total de tareas

6 tareas. Grafo de dependencias:

```text
T1 ─┐
    │
T2 ─┴──► T3 ──► T4 ─┐
                    ├─► T6
              T5 ───┘
```

T1 y T2 pueden correr en paralelo desde el inicio (archivos disjuntos:
`shared/core/` vs `shared/db/`). T4 y T5 pueden correr en paralelo
tras T3 (archivos disjuntos: `services/tracking_pixel/` vs
`services/contact_form/`).

Granularidad: medium (6 tareas). Adecuada para 1-2 devs en paralelo
(T1+T2 al inicio, T4+T5 tras T3).

[← Archivos afectados](03-archivos-afectados.md) | [Siguiente: Commits →](05-commits.md)
