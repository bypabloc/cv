# 03 — Commits

[← 02-implementacion.md](02-implementacion.md) | [04-paralelizacion-worktrees.md →](04-paralelizacion-worktrees.md)

## 9. Commits

Cada commit deja el repo verde (lint + typecheck + tests del scope) y
es revisable atomicamente. Mensajes Conventional Commits en espanol.

Orden NO negociable:

```text
0. crear rama feature/drop-cloudfront-meta desde dev
1. docs(specs)        — crear la carpeta del plan
2. feat(db)           — migracion alembic
3. refactor(db-models)— drop columnas SQLAlchemy
4. refactor(lambda)   — drop persistencia tracking_pixel
5. refactor(lambda)   — drop persistencia contact_form
6. test(lambda)       — actualizar unit tests
7. verify(spec)       — bateria E2E + git rm de la carpeta del plan
```

---

### Commit 0 — preparar rama de trabajo

```bash
# verificar rama actual
branch=$(git branch --show-current)
case "$branch" in
  dev|stage|main|master)
    git checkout -b feature/drop-cloudfront-meta
    ;;
esac
```

NO es un commit; es el gate antes del primer commit. La rama parte de
`dev`.

---

### Commit 1 — `docs(specs): plan drop-cloudfront-meta`

**Scope**: solo `docs/specs/drop-cloudfront-meta/` (6 archivos creados).

**Mensaje**:

```text
docs(specs): plan drop-cloudfront-meta

- Carpeta del plan en docs/specs/drop-cloudfront-meta/ (6 archivos)
- Drop forward de 6 columnas huerfanas en Neon:
  * tracking_events: cloudfront_meta, expires_at, page_url, page_title,
    referrer
  * contacts: cloudfront_meta
- Drop del indice parcial idx_tracking_referrer
- page_path SE MANTIENE (canonica para analitica por seccion)
- Pydantic + frontend NO se tocan (decision: aceptar y descartar)
- Helper extract_cloudfront_meta + inyeccion en http_dispatch se
  mantienen (codigo muerto controlado)
- Migracion alembic con down_revision = 'b2c3d4e5f6a7'
```

**Verificacion incremental**: `git diff --stat HEAD` muestra solo
archivos de `docs/specs/`. Sin tests, no rompe nada.

---

### Commit 2 — `feat(db): migracion alembic drop columnas huerfanas + idx_tracking_referrer`

**Scope**:

- `serverless/lambda/shared/db/alembic/versions/<rev>_drop_cloudfront_expires_page_fields.py`
  (archivo creado).

**Mensaje**:

```text
feat(db): drop columnas huerfanas y idx_tracking_referrer en alembic

- Nueva revision con down_revision = 'b2c3d4e5f6a7'
- upgrade(): drop_index idx_tracking_referrer
- upgrade(): drop_column cloudfront_meta en tracking_events y contacts
- upgrade(): drop_column expires_at, page_url, page_title, referrer
  en tracking_events
- downgrade(): recrea las 6 columnas nullable + el indice parcial.
  page_url vuelve como NULL (no NOT NULL) para que el revert no rompa
  si hay rows nuevas.
- expires_at en DynamoDB cache + rate_limit_bucket + TrackingEventItem
  fixture NO se toca (TTL real con consumer activo)
- page_path NO se toca (canonica para analitica por seccion)
```

**Verificacion incremental**:

```bash
# 1. branch Neon de prueba
neon branches create --name test-drop-cfm-expires --parent main
DATABASE_URL=<branch-url> \
  .venv/bin/alembic -c shared/db/alembic.ini upgrade head
DATABASE_URL=<branch-url> \
  .venv/bin/alembic -c shared/db/alembic.ini downgrade -1
DATABASE_URL=<branch-url> \
  .venv/bin/alembic -c shared/db/alembic.ini upgrade head
neon branches delete test-drop-cfm-expires
# 2. compilacion
python -m compileall -q serverless/lambda/shared/db/alembic
```

---

### Commit 3 — `refactor(db-models): drop columnas huerfanas en ORM`

**Scope**:

- `serverless/lambda/shared/db/models/tracking.py`
- `serverless/lambda/shared/db/models/contact.py`

**Mensaje**:

```text
refactor(db-models): drop columnas huerfanas en ORM

- tracking_events: drop expires_at, page_url, page_title, referrer,
  cloudfront_meta del modelo TrackingEvent
- tracking_events: drop entrada idx_tracking_referrer de __table_args__
- contacts: drop columna cloudfront_meta del modelo Contact
- page_path y su idx_tracking_page_path NO se tocan
- Modelos quedan alineados al schema post-upgrade del alembic
```

**Verificacion incremental**:

```bash
python -m compileall -q serverless/lambda/shared/db/models
python devtools/run.py serverless tests --type=unit --lambda=db
```

---

### Commit 4 — `refactor(lambda): drop persistencia huerfana en tracking_pixel`

**Scope**:

- `serverless/lambda/services/tracking_pixel/core/services/tracking_service.py`
- `serverless/lambda/services/tracking_pixel/core/controllers/tracking/track.py`

**Mensaje**:

```text
refactor(lambda): drop persistencia huerfana en tracking_pixel

- tracking_service.process_tracking_event ya no acepta cloudfront_meta
  como kwarg
- save_tracking_event ya no emite expires_at, cloudfront_meta, page_url,
  page_title ni referrer en el dict que insert_tracking persiste
- track controller ya no propaga meta.cloudfront_meta al service
- TrackEventMeta.cloudfront_meta y TrackEventModel.page_url/page_title/
  referrer se mantienen (Pydantic acepta los valores pero nadie los lee
  downstream — decision del plan)
- Frontend (build-track-payload, TrackingPixel.astro) no cambia
- Docstrings actualizadas
```

**Verificacion incremental**:

```bash
python devtools/run.py serverless tests --type=unit --lambda=tracking_pixel
```

---

### Commit 5 — `refactor(lambda): drop persistencia cloudfront_meta en contact_form`

**Scope**:
- `serverless/lambda/services/contact_form/core/services/contact_service.py`
- `serverless/lambda/services/contact_form/core/models/contact.py`

**Mensaje**:

```text
refactor(lambda): drop cloudfront_meta en contact_form

- contact_service.save_contact ya no emite cloudfront_meta en el dict
  que insert_contact persiste
- ContactCreateModel.form_fields() ya no inyecta cloudfront_meta en su
  output
- RequestMeta.cloudfront_meta se mantiene (decision del plan)
- Docstrings actualizadas
```

**Verificacion incremental**:

```bash
python devtools/run.py serverless tests --type=unit --lambda=contact_form
```

---

### Commit 6 — `test(lambda): actualiza unit + integration tests post drop`

**Scope**:

- `serverless/lambda/services/tracking_pixel/tests/unit/test_save_tracking_event_persists_item.py`
- `serverless/lambda/services/tracking_pixel/tests/integration/test_valid_event_persists_e2e.py`
- cualquier otro test cuyo assert se rompa por el drop (a identificar
  al ejecutar la bateria; si surge, queda en este commit).

**Mensaje**:

```text
test(lambda): actualiza tests post drop columnas huerfanas

- test_save_tracking_event_persists_item: reemplaza asserts de
  expires_at, page_url, cloudfront_meta por 'not in payload' para las
  5 keys dropeadas
- test_valid_event_persists_e2e (integration): elimina asserts de
  item['page_url'] y item['page_title'] (columnas ya no existen)
- Tests de extract_cloudfront_meta, http_handler_injects_meta_from_headers
  y tracking_payload (que asserta page_title del Pydantic) NO se tocan
- Tests con page_url en fixtures (rejects_missing_session_id, etc) NO
  se tocan: el campo Pydantic sigue vigente
```

**Verificacion incremental**:

```bash
python devtools/run.py serverless tests --type=unit --lambda=tracking_pixel
python devtools/run.py serverless tests --type=unit --lambda=contact_form
python devtools/run.py serverless tests --type=coverage --lambda=tracking_pixel
python devtools/run.py serverless tests --type=coverage --lambda=contact_form
```

---

### Commit 7 — `verify(spec): bateria E2E + cleanup del plan`

**Scope**:
- Eliminar la carpeta `docs/specs/drop-cloudfront-meta/` (con
  `git rm -r`).
- Cualquier ajuste de ultimo momento detectado por la bateria.

**Mensaje**:

```text
verify(spec): drop-cloudfront-meta bateria E2E + cleanup

- bateria completa de la seccion 11 ejecutada en verde
- git rm -r docs/specs/drop-cloudfront-meta/ (plan efimero, se elimina
  al cerrar)
```

**Verificacion incremental**: ver
[05-verificacion-e2e.md](05-verificacion-e2e.md) — bateria completa
debe pasar en VERDE antes de aceptar este commit.

---

## Resumen de secuencia

```text
commit 0 (no-commit) → checkout feature/drop-cloudfront-meta
commit 1 → docs(specs): plan
commit 2 → feat(db): migracion alembic
commit 3 → refactor(db-models): SQLAlchemy
commit 4 → refactor(lambda): tracking_pixel
commit 5 → refactor(lambda): contact_form
commit 6 → test(lambda): unit tests
commit 7 → verify(spec): bateria + git rm del plan
```

Un solo PR: `feature/drop-cloudfront-meta -> dev`. Despues, promocion
en cadena `dev -> stage -> main` siguiendo
[.claude/rules/git-workflow.md](../../../.claude/rules/git-workflow.md).

---

[← 02-implementacion.md](02-implementacion.md) | [04-paralelizacion-worktrees.md →](04-paralelizacion-worktrees.md)
