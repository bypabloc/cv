# 05 — Secuencia de commits

[← Descomposicion](04-descomposicion.md) | [Siguiente: Paralelizacion →](06-paralelizacion-worktrees.md)

Conventional Commits espanol. Cada commit deja el repo verde
(lint + typecheck + tests del scope). PR unico
`feature/sessions-normalize -> dev`.

## Secuencia

### C1 — `docs(specs): plan sessions-normalize`

- Crea `docs/specs/sessions-normalize/` (este readme + 01-07).
- Cubre: decisiones, schema, descomposicion, plan de commits, verificacion.
- Verificacion incremental: `pnpm exec biome check .` (linter de markdown / no debe romperse), `python3 -m yaml.safe_load` (no aplica), inspeccion manual.

### C2 — `feat(db): introduce sessions + session_visits en alembic`

- Crea la migration `d4e5f6a7b8c9_introduce_sessions_visits.py`.
- `upgrade()`: TRUNCATE `tracking_events` + `contacts`, CREATE TABLE
  `sessions`, CREATE TABLE `session_visits`, DROP COLUMNs viejas,
  ADD FKs.
- `downgrade()`: invierte (ADD COLUMNs nullable, DROP FKs, DROP TABLEs).
- AC cubiertos: AC-8, AC-9, AC-10, AC-11.
- Verificacion: en branch Neon de prueba `alembic upgrade head` y
  `alembic downgrade -1` corren clean (idempotente). Snapshot schema
  via `psql`.

### C3 — `refactor(db-models): introduce Session y SessionVisit; drop columnas en TrackingEvent y Contact`

- Crea `shared/db/models/session.py` + `session_visit.py`.
- Modifica `tracking.py` (drop columnas + agrega FKs `session_id`/`visit_id`).
- Modifica `contact.py` (drop columnas + ALTER session_id NOT NULL + FK).
- Modifica `__init__.py` (re-exporta).
- Verificacion: `python -m compileall -q serverless/lambda/shared/db/models/`, imports validos, `serverless tests --type=unit --lambda=tracking_pixel` y `--lambda=contact_form` SI todos los tests que dependen de las columnas dropeadas ya estan adaptados — caso contrario, C3 deja tests rojos que C4/C5/C6 arreglan.

### C4 — `feat(db): repository helper ensure_session_and_visit`

- Modifica `shared/db/repository.py` agregando el helper.
- Re-exporta desde `shared/db/__init__.py`.
- AC: AC-1, AC-2, AC-3, AC-4.
- Verificacion: unit tests del helper (in-memory PG via testcontainers
  o equivalente) cubren AC-1/2/3/4 -> verde.

### C5 — `feat(http): niche_from_origin helper`

- Crea `shared/http/niche.py` con `niche_from_origin(origin) -> str | None`.
- AC: AC-6 (parcial).
- Verificacion: unit test estandalone valida los 6 niches conocidos +
  Origin desconocido -> None.

### C6 — `refactor(lambda): tracking_pixel usa ensure_session_and_visit`

- Modifica `tracking_pixel/core/services/tracking_service.py` y
  `controllers/tracking/track.py`.
- Agrega/actualiza tests unit (3 nuevos) + integration (1
  actualizado).
- AC: AC-1, AC-2, AC-3, AC-4, AC-5, AC-12.
- Verificacion: `serverless tests --type=unit --lambda=tracking_pixel`
  + `--type=integration --lambda=tracking_pixel` -> verde.

### C7 — `refactor(lambda): contact_form usa ensure_session_and_visit + niche fallback`

- Modifica `contact_form/core/services/contact_service.py` y
  `controllers/contact/create.py`.
- Agrega/actualiza tests unit (2 nuevos) + integration (1
  actualizado o creado).
- AC: AC-6, AC-7, AC-9, AC-12.
- Verificacion: `serverless tests --type=unit --lambda=contact_form`
  + `--type=integration --lambda=contact_form` -> verde.

### C8 — `verify(spec): sessions-normalize bateria E2E + cleanup`

- Borra `docs/specs/sessions-normalize/` (`git rm -r`).
- Ejecuta la bateria de comandos de
  [07-verificacion-e2e.md](07-verificacion-e2e.md):
  - `serverless deploy --stage=dev --lambda=db` (migrate)
  - `serverless deploy --stage=dev --lambda=tracking_pixel`
  - `serverless deploy --stage=dev --lambda=contact_form`
  - curls realistas de /track + /contact
  - psql queries para verificar las 3 tablas y las FKs
  - inspeccion CloudWatch: cero `NotNullViolation` ni
    `ForeignKeyViolation` post-deploy
- Verificacion: bateria pasa completa en verde.

## Regla por commit

- Cada commit deja `dev` (la base) buildable + tests verdes EN SU
  SCOPE. C3 puede dejar tests de C6/C7 rojos temporalmente porque
  fueron escritos contra el modelo viejo — eso se permite SI y solo si
  C6 y C7 (que siguen en la misma rama) los arreglan en la misma PR.
- Antes del push -> PR, la bateria E2E de C8 debe pasar.
- NO push y NO crear PR hasta C8 verde (regla de
  [plan-format.md](.claude/rules/plan-format.md)).

## Resumen de secuencia

```
C1 (plan) ──► C2 (migration) ──► C3 (modelos) ──► C4 (helper) ──► C5 (niche helper)
                                                                       │
                                                              ┌────────┴────────┐
                                                              ▼                 ▼
                                                       C6 (tracking)     C7 (contact)
                                                              │                 │
                                                              └────────┬────────┘
                                                                       ▼
                                                              C8 (verify + cleanup)
```

C6 y C7 son paralelizables (ver [06](06-paralelizacion-worktrees.md)).
El resto es lineal.

## PR

Titulo: `feat(db): normaliza schema con sessions + session_visits`.

Body sigue el template del proyecto:

- **Problema**: redundancia de session_id/ip/ua/utm en tracking_events
  y contacts; perdida de info multi-touch.
- **Solucion**: 3 tablas (sessions + session_visits + tracking_events
  con FKs); helper `ensure_session_and_visit` en repo compartido;
  niche fallback via Origin header en contact_form. TRUNCATE en todos
  los stages (decision 3).
- **Como probar**: la bateria E2E de C8 (ver [07](07-verificacion-e2e.md)).
- **TODO**: ninguno.

[← Descomposicion](04-descomposicion.md) | [Siguiente: Paralelizacion →](06-paralelizacion-worktrees.md)
