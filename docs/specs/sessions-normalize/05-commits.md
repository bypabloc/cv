# 05 — Secuencia de commits

[← Descomposicion](04-descomposicion.md) | [Siguiente: Paralelizacion →](06-paralelizacion-worktrees.md)

Conventional Commits espanol. Cada commit deja el repo verde
(lint + typecheck + tests del scope). PR unico
`feature/sessions-normalize -> dev`.

## Secuencia

### C1 — `docs(specs): plan sessions-normalize`

- Crea `docs/specs/sessions-normalize/` (este readme + 01-07).
- Cubre: decisiones, schema, descomposicion, plan de commits,
  verificacion.
- Verificacion incremental: `pnpm exec biome check .` (linter de
  markdown / no debe romperse), inspeccion manual.

### C2 — `refactor(shared): centraliza niches en shared/core/niches.py`

- Crea `shared/core/niches.py` con `ALL_NICHES`, `CV_NICHES`,
  `niche_from_origin`.
- Re-exporta desde `shared/core/__init__.py`.
- Migra `services/cv/core/models/cv.py` para importar `CV_NICHES`
  (elimina `_VALID_NICHES` local).
- Crea `shared/tests/unit/core/test_niches.py` (cubre AC-13).
- AC: AC-13, AC-14.
- Verificacion:
  - `python -m pytest serverless/lambda/shared/tests/unit/core/test_niches.py -v` -> verde.
  - `serverless tests --type=unit --lambda=cv --aws-profile=tfs-dev` -> verde.
  - `rg -n "_VALID_NICHES" serverless/lambda/` -> 0 lineas.

### C3 — `feat(db): introduce sessions + session_visits en alembic`

- Crea la migration `d4e5f6a7b8c9_introduce_sessions_visits.py`.
- `upgrade()`: TRUNCATE `tracking_events` + `contacts`, CREATE TABLE
  `sessions`, CREATE TABLE `session_visits` (con `event_count INTEGER
  NOT NULL DEFAULT 0`), DROP COLUMNs viejas, ADD FKs.
- `downgrade()`: invierte (ADD COLUMNs nullable, DROP FKs, DROP TABLEs).
- AC cubiertos: AC-8, AC-9, AC-10, AC-11.
- Verificacion: en branch Neon de prueba `alembic upgrade head` y
  `alembic downgrade -1` corren clean (idempotente). Snapshot schema
  via `psql`. Confirmar `event_count` esta con `DEFAULT 0 NOT NULL`.

### C4 — `refactor(db-models): introduce Session y SessionVisit; drop columnas en TrackingEvent y Contact`

- Crea `shared/db/models/session.py` + `session_visit.py` (este
  ultimo incluye `event_count` como `Mapped[int]`).
- Modifica `tracking.py` (drop columnas + agrega FKs
  `session_id`/`visit_id`).
- Modifica `contact.py` (drop columnas + ALTER session_id NOT NULL + FK).
- Modifica `__init__.py` (re-exporta).
- Verificacion: `python -m compileall -q serverless/lambda/shared/db/models/`, imports validos.

### C5 — `feat(db): repository helper ensure_session_and_visit`

- Modifica `shared/db/repository.py` agregando el helper con flag
  `bump_event_count` (default `True`). El helper incrementa
  `event_count` en la misma tx (decision 12).
- Re-exporta desde `shared/db/__init__.py`.
- AC: AC-1, AC-2, AC-3, AC-4, AC-15.
- Verificacion: unit tests del helper (in-memory PG via
  testcontainers o equivalente) cubren AC-1/2/3/4/15 -> verde.

### C6 — `refactor(lambda): tracking_pixel usa ensure_session_and_visit`

- Modifica `tracking_pixel/core/services/tracking_service.py` y
  `controllers/tracking/track.py`.
- Agrega/actualiza tests unit (4 nuevos: idempotencia, ip-change,
  utm-change table-driven con 5 UTM, event_count invariant) +
  integration (1 actualizado).
- AC: AC-1, AC-2, AC-3, AC-4, AC-5, AC-12, AC-15, AC-16.
- Verificacion: `serverless tests --type=unit --lambda=tracking_pixel`
  y `--type=integration --lambda=tracking_pixel` -> verde.

### C7 — `refactor(lambda): contact_form usa ensure_session_and_visit + niche fallback`

- Modifica `contact_form/core/services/contact_service.py` y
  `controllers/contact/create.py`.
- Importa `niche_from_origin` de `shared.core.niches` (NO crea modulo
  nuevo: ya existe desde C2).
- Agrega/actualiza tests unit (2 nuevos) + integration (1 actualizado
  o creado).
- AC: AC-6, AC-7, AC-9, AC-12.
- Verificacion: `serverless tests --type=unit --lambda=contact_form`
  y `--type=integration --lambda=contact_form` -> verde.

### C8 — `verify(spec): sessions-normalize bateria E2E + cleanup`

- Borra `docs/specs/sessions-normalize/` (`git rm -r`).
- Ejecuta la bateria de comandos de
  [07-verificacion-e2e.md](07-verificacion-e2e.md):
  - `serverless deploy --stage=dev --lambda=db` (migrate)
  - `serverless deploy --stage=dev --lambda=tracking_pixel`
  - `serverless deploy --stage=dev --lambda=contact_form`
  - `serverless deploy --stage=dev --lambda=cv` (porque C2 modifico
    el modelo)
  - curls realistas de /track + /contact
  - psql queries para verificar las 3 tablas, las FKs y la invariante
    `event_count == COUNT(*)` (AC-16)
  - inspeccion CloudWatch: cero `NotNullViolation` ni
    `ForeignKeyViolation` post-deploy
- Verificacion: bateria pasa completa en verde.

## Regla por commit

Cada commit deja `dev` (la base) buildable + tests verdes EN SU
SCOPE. C4 puede dejar tests de C6/C7 rojos temporalmente porque
fueron escritos contra el modelo viejo — eso se permite SI y solo si
C6 y C7 (que siguen en la misma rama) los arreglan en la misma PR.

Antes del push -> PR, la bateria E2E de C8 debe pasar.

NO push y NO crear PR hasta C8 verde (regla de
[plan-format.md](.claude/rules/plan-format.md)).

## Resumen de secuencia

```text
C1 (plan)
  │
  ├──► C2 (niches central) ─┐
  │                          │
  └──► C3 (migration) ─► C4 (modelos) ─► C5 (helper)
                                            │
                                  ┌─────────┴─────────┐
                                  ▼                   ▼
                            C6 (tracking)       C7 (contact)
                                  │                   │
                                  └────────┬──────────┘
                                           ▼
                                  C8 (verify + cleanup)
```

C2 y C3 son paralelizables desde el inicio (archivos disjuntos:
`shared/core/` vs `shared/db/alembic/`). C6 y C7 son paralelizables
tras C5 (ver [06](06-paralelizacion-worktrees.md)). El resto es
lineal.

## PR

Titulo: `feat(db): normaliza schema con sessions + session_visits`.

Body sigue el template del proyecto:

- **Problema**: redundancia de session_id/ip/ua/utm en tracking_events
  y contacts; perdida de info multi-touch; `_VALID_NICHES` duplicado
  en `cv` y frontend.
- **Solucion**: 3 tablas (sessions + session_visits + tracking_events
  con FKs) con `event_count` denormalizado para analitica; helper
  `ensure_session_and_visit` en repo compartido; modulo central de
  niches en `shared/core/niches.py` (`ALL_NICHES`, `CV_NICHES`,
  `niche_from_origin`); niche fallback via Origin header en
  contact_form. TRUNCATE en todos los stages (decision 3).
- **Como probar**: la bateria E2E de C8 (ver [07](07-verificacion-e2e.md)).
- **TODO**: opcional — migrar el frontend (`packages/content/src/lib/cv-api-client.ts:26`) para que importe los niches del backend via un build-time fetch o un constants file compartido, eliminando la ultima duplicacion.

[← Descomposicion](04-descomposicion.md) | [Siguiente: Paralelizacion →](06-paralelizacion-worktrees.md)
