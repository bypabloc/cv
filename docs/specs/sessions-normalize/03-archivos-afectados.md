# 03 — Archivos afectados (con verificacion por archivo)

[← ER](02-diagrama-er.md) | [Siguiente: Descomposicion →](04-descomposicion.md)

Paths relativos desde root. Cada archivo tiene un comando de
verificacion explicito. La spec se considera completa solo cuando
todos los comandos de verificacion pasan.

## Fase 1 — Centralizar niches en `shared/core/niches.py`

Hallazgo del audit pre-spec (ver
[01-contexto-y-decisiones.md](01-contexto-y-decisiones.md#hallazgo-del-audit-niches-duplicados-en-backend--frontend)):
`_VALID_NICHES` esta duplicado en `services/cv/core/models/cv.py` y
disperso en el frontend. Antes de tocar nada del schema, se introduce
un modulo central como unica fuente de verdad de los 6 niches del
portfolio.

### Crear fase 1

- `serverless/lambda/shared/core/niches.py` — modulo nuevo. Expone
  `ALL_NICHES` (frozenset de 6), `CV_NICHES` (frozenset de 5,
  excluye `hub`), y `niche_from_origin(origin: str | None) -> str | None`.
  - Verificar: `python -c "from shared.core.niches import ALL_NICHES, CV_NICHES, niche_from_origin; assert len(ALL_NICHES) == 6; assert len(CV_NICHES) == 5; assert 'hub' in ALL_NICHES; assert 'hub' not in CV_NICHES"`.
  - Verificar: `python -c "from shared.core.niches import niche_from_origin; assert niche_from_origin('https://fintech.portfolio.dev.the-full-stack.com') == 'fintech'; assert niche_from_origin('https://the-full-stack.com') is None; assert niche_from_origin(None) is None"`.

### Modificar fase 1

- `serverless/lambda/shared/core/__init__.py` — re-exportar
  `ALL_NICHES`, `CV_NICHES`, `niche_from_origin` (mantener
  consistencia con el patron de `shared/core/exceptions.py` etc.).
  - Verificar: `python -c "from shared.core import ALL_NICHES, CV_NICHES, niche_from_origin"`.
- `serverless/lambda/services/cv/core/models/cv.py` — eliminar el
  `_VALID_NICHES` local (linea 18) y reemplazar el `in _VALID_NICHES`
  por `in CV_NICHES` importado de `shared.core.niches`.
  - Verificar: `rg -n "_VALID_NICHES" serverless/lambda/services/cv/` devuelve 0 lineas.
  - Verificar: `serverless tests --type=unit --lambda=cv --aws-profile=tfs-dev` -> verde (los tests existentes de filtrado por niche siguen pasando con la nueva fuente).

### Tests fase 1

- `serverless/lambda/shared/tests/unit/core/test_niches.py` (NUEVO) —
  cubre AC-13: `ALL_NICHES`/`CV_NICHES` exactos,
  `niche_from_origin` para los 6 niches validos + Origin invalido +
  None.
  - Verificar: el test corre en la suite de `shared/` (si existe) o se
    integra al unit-runner del proyecto. Comando: `python -m pytest
    serverless/lambda/shared/tests/unit/core/test_niches.py -v`.

## Fase 2 — Migration Alembic + modelos ORM

### Crear fase 2

- `serverless/lambda/shared/db/alembic/versions/d4e5f6a7b8c9_introduce_sessions_visits.py`
  — migration nueva. `upgrade()`: TRUNCATE tracking + contacts, CREATE
  TABLE sessions, CREATE TABLE session_visits (incluye
  `event_count INTEGER NOT NULL DEFAULT 0`), DROP COLUMNs viejas,
  ADD FKs. `downgrade()`: ADD COLUMNs (nullable), DROP FKs,
  DROP TABLE session_visits, DROP TABLE sessions.
  - Verificar: `serverless run --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev` retorna `status=ok` y `current=d4e5f6a7b8c9 (head)`.
  - Verificar: `psql ... -c "SELECT to_regclass('sessions'), to_regclass('session_visits');"` retorna ambas tablas.
  - Verificar: `psql ... -c "SELECT column_name FROM information_schema.columns WHERE table_name='session_visits' AND column_name='event_count';"` devuelve 1 row con `is_nullable=NO` y `column_default='0'`.
  - Verificar: `psql ... -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='tracking_events' AND column_name IN ('ip','country','user_agent','browser','utm_source');"` retorna 0.
- `serverless/lambda/shared/db/models/session.py` — modelo `Session`
  con `session_id` PK, `first_seen_at`, `last_seen_at`, identidad.
  - Verificar: `python -m compileall -q serverless/lambda/shared/db/models/session.py`.
- `serverless/lambda/shared/db/models/session_visit.py` — modelo
  `SessionVisit` con `visit_id` PK + `session_id` FK + `event_count`
  (`Mapped[int]` con `server_default=text('0')`).
  - Verificar: idem.

### Modificar fase 2

- `serverless/lambda/shared/db/models/__init__.py` — re-exportar
  `Session`, `SessionVisit`.
  - Verificar: `python -c "from shared.db.models import Session, SessionVisit"`.
- `serverless/lambda/shared/db/models/tracking.py` — drop columnas
  movidas, agregar `visit_id` Mapped, agregar `ForeignKey('sessions.session_id')` y `ForeignKey('session_visits.visit_id')` en las columnas. Drop entradas del `__table_args__` que indexan columnas eliminadas (`idx_tracking_utm_source`, `idx_tracking_country`, `idx_tracking_device_type`).
  - Verificar: `python -m compileall -q serverless/lambda/shared/db/models/tracking.py`.
  - Verificar: `python -c "from shared.db.models.tracking import TrackingEvent; assert 'utm_source' not in TrackingEvent.__table__.columns.keys()"`.
- `serverless/lambda/shared/db/models/contact.py` — drop columnas
  `ip`, `country`, `user_agent`, ALTER `session_id` a `nullable=False`
  y agregar `ForeignKey('sessions.session_id')`. Drop el `WHERE session_id IS NOT NULL` del indice (ahora siempre NOT NULL).
  - Verificar: `python -m compileall -q serverless/lambda/shared/db/models/contact.py`.

## Fase 3 — Repository helper

### Modificar fase 3

- `serverless/lambda/shared/db/repository.py` — agregar
  `ensure_session_and_visit(session, *, session_id, ip, country,
  user_agent, browser, browser_version, os_name, device_type,
  utm_source, utm_medium, utm_campaign, utm_content, utm_term,
  referrer, landing_page_path, niche, bump_event_count=True) ->
  tuple[str, str]`.
  - Implementacion:
    1. `INSERT INTO sessions (...) ON CONFLICT (session_id) DO UPDATE SET last_seen_at = now() RETURNING session_id`.
    2. `SELECT visit_id, ip, utm_source, utm_medium, utm_campaign, utm_content, utm_term FROM session_visits WHERE session_id = :sid ORDER BY started_at DESC LIMIT 1 FOR UPDATE`.
    3. Si vacio O cualquiera de `(ip, utm_source, utm_medium, utm_campaign, utm_content, utm_term)` distinto: `INSERT INTO session_visits (..., event_count) VALUES (..., CASE WHEN :bump THEN 1 ELSE 0 END) RETURNING visit_id`. Si igual: `UPDATE session_visits SET ended_at = now(), event_count = event_count + CASE WHEN :bump THEN 1 ELSE 0 END WHERE visit_id = :vid RETURNING visit_id`.
  - Verificar: `serverless tests --type=unit --lambda=tracking_pixel` y `--lambda=contact_form` con tests nuevos que cubren AC-1 / AC-2 / AC-3 / AC-4 / AC-15.
- `serverless/lambda/shared/db/__init__.py` — re-exportar
  `ensure_session_and_visit`.
  - Verificar: `python -c "from shared.db import ensure_session_and_visit"`.

## Fase 4 — `tracking_pixel`: integrar el helper

### Modificar fase 4

- `serverless/lambda/services/tracking_pixel/core/services/tracking_service.py`
  — `save_tracking_event` ahora llama `ensure_session_and_visit`
  (con `bump_event_count=True`) ANTES del `session.add(TrackingEvent(...))`. El dict del INSERT YA NO incluye las columnas movidas (ya no van como kwargs). El `visit_id` retornado se pasa al `TrackingEvent`. `process_tracking_event` arma el payload incluyendo `referrer` y `landing_page_path` (= `page_path` del primer event de la visit) para que el helper pueda crear el visit con el landing correcto.
  - Verificar: `serverless tests --type=unit --lambda=tracking_pixel`.
  - Verificar: `serverless tests --type=integration --lambda=tracking_pixel`.
- `serverless/lambda/services/tracking_pixel/core/controllers/tracking/track.py`
  — pasar `referrer` y `landing_page_path` al service.
  - Verificar: idem unit + integration.
- `serverless/lambda/services/tracking_pixel/core/models/tracking.py`
  — `TrackEventModel.tracking_payload()` ya emite los campos
  necesarios (page_url -> landing_page_path; referrer ya esta). Sin
  cambios estructurales esperados; verificar que `referrer` siga
  pasandose.
  - Verificar: unit tests del modelo.

### Tests fase 4

- `serverless/lambda/services/tracking_pixel/tests/unit/test_save_tracking_event_persists_item.py` — actualizar para validar que se crearon (sessions + session_visits + tracking_events) en la misma tx y que `event_count` quedo en 1 (AC-1).
  - Verificar: corre verde.
- `serverless/lambda/services/tracking_pixel/tests/unit/test_session_upsert_idempotent.py` (NUEVO) — AC-2 (mismo `(ip, utm_*)` -> reusa visit y `event_count` se incrementa a 2 en el segundo evento).
  - Verificar: corre verde.
- `serverless/lambda/services/tracking_pixel/tests/unit/test_visit_creates_on_ip_change.py` (NUEVO) — AC-3.
  - Verificar: corre verde.
- `serverless/lambda/services/tracking_pixel/tests/unit/test_visit_creates_on_utm_change.py` (NUEVO) — AC-4. Cubre los 5 UTM (source, medium, campaign, content, term) con una table-driven test.
  - Verificar: corre verde.
- `serverless/lambda/services/tracking_pixel/tests/unit/test_event_count_matches_count_invariant.py` (NUEVO) — AC-15/AC-16: tras N events en una misma visit, `event_count == N`.
  - Verificar: corre verde.
- `serverless/lambda/services/tracking_pixel/tests/integration/test_valid_event_persists_e2e.py` — actualizar AC-1/AC-5: asserts post-INSERT verifican rows en las 3 tablas correctamente enlazadas + `event_count == 1`.
  - Verificar: `serverless tests --type=integration --lambda=tracking_pixel`.

## Fase 5 — `contact_form`: integrar el helper + niche fallback

### Modificar fase 5

- `serverless/lambda/services/contact_form/core/services/contact_service.py`
  — `save_contact` llama `ensure_session_and_visit` (con
  `bump_event_count=True` — un contact tambien suma al contador del
  visit) antes del INSERT en `contacts`. Si no hay UTM/referrer/
  landing en el contact payload (no los envia el form), se pasan
  como `None`. El service NO persiste mas `ip`, `country`,
  `user_agent` directamente en `contacts` — solo via la session.
  - Verificar: unit tests + integration tests pasan.
- `serverless/lambda/services/contact_form/core/controllers/contact/create.py`
  — agrega resolucion del `niche` cuando no viene en el payload del
  form: extraer del header `Origin` usando `niche_from_origin` de
  `shared.core.niches` (centralizado en Fase 1).
  - Verificar: nuevo unit test cubre AC-6.

NOTA: el helper `niche_from_origin` se crea en Fase 1, NO aqui. Esta
fase solo lo importa y usa. Esto cumple "Interface Stability" para
permitir paralelizacion (Fase 4 y Fase 5 son worktree-safe tras Fase 1
y Fase 3).

### Tests fase 5

- `serverless/lambda/services/contact_form/tests/unit/test_contact_creates_session_on_the_fly.py` (NUEVO) — AC-6: contact sin track previo crea session + visit. Mockea ip/ua del request, verifica que `niche` se infiere del Origin header via `niche_from_origin`.
  - Verificar: corre verde.
- `serverless/lambda/services/contact_form/tests/unit/test_contact_reuses_existing_session.py` (NUEVO) — AC-7: contact con session previa reusa.
  - Verificar: corre verde.
- `serverless/lambda/services/contact_form/tests/integration/test_contact_persists_e2e.py` (existente, si aplica, o crear) — verifica las 3 inserts en la misma tx + `event_count` del visit final coherente con (events de tracking + contact).
  - Verificar: integration tests verdes.

## Fase 6 — Verificacion E2E (deploy + curls + queries)

Detalle en [07-verificacion-e2e.md](07-verificacion-e2e.md). Resumen:

- `serverless deploy --stage=dev --lambda=db --aws-profile=tfs-dev` — corre la migration en Neon dev.
- `serverless deploy --stage=dev --lambda=tracking_pixel --aws-profile=tfs-dev` + `--lambda=contact_form` + `--lambda=cv` (este ultimo porque Fase 1 modifico el modelo).
- `curl POST /track` con payload realista -> verificar `HTTP 204`, row en `tracking_events` + `sessions` + `session_visits` con `event_count=1`.
- `curl POST /contact` con bypass de Turnstile (o desde browser) -> verificar `HTTP 200`, row en `contacts` enlazada via FK.
- Multi-visit: 2 curls /track con utm distinto -> verificar 2 rows en `session_visits` para mismo `session_id` con `event_count=1` cada uno.
- Invariante AC-16: query SQL post-pruebas confirma `event_count == COUNT(*)` para cada visit.

[← ER](02-diagrama-er.md) | [Siguiente: Descomposicion →](04-descomposicion.md)
