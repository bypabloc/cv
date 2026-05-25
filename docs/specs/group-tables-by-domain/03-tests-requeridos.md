# 03 — Tests Requeridos

[README](README.md) | [02-diagrama-er](02-diagrama-er.md) |
**03-tests** | [04-archivos-afectados](04-archivos-afectados.md)

Todos los tests usan TDD (escribir rojo primero). Cada test referencia
al menos un AC entre corchetes.

## 6.A — TDD flows nuevos

### `serverless/lambda/shared/db/seeds_helpers.py` (helper de parsing de fecha)

- WHEN `_parse_ym("2024-01")` THEN retorna `date(2024, 1, 1)` [AC-2]
- WHEN `_parse_ym("2024-01-15")` THEN retorna `date(2024, 1, 15)` [AC-2]
- WHEN `_parse_ym(None)` THEN retorna `None` [AC-2]
- WHEN `_parse_ym("invalid")` THEN levanta `ValueError` [AC-2]

## 6.B — Unit tests (pytest)

### `serverless/lambda/shared/db/models/`

Tests por subcarpeta. Path mirroring:
`shared/db/models/cv/profile.py` -> `shared/tests/db/models/cv/test_profile.py`.

- WHEN `Profile.__tablename__` THEN es `'cv_profiles'` [AC-1]
- WHEN `Profile.__module__` THEN incluye `.cv.profile` [AC-8]
- WHEN `Contact.__tablename__` THEN es `'vis_contacts'` [AC-1]
- WHEN `Niche.__tablename__` THEN es `'tax_niches'` [AC-1]
- WHEN `Translation.__tablename__` THEN es `'i18n_translations'` [AC-1]
- WHEN `Endorsement.__tablename__` THEN es `'cv_endorsements'` [AC-1, AC-9]
- WHEN `EducationEntry.__tablename__` THEN es `'cv_education_entries'` [AC-1]
- WHEN `Experience` declara columnas THEN incluye `started_on: Mapped[date]` y `ended_on: Mapped[date | None]` (no `start_ym`) [AC-2]
- WHEN `Skill` declara columnas THEN incluye `slug: Mapped[str]` con UK [AC-4]
- WHEN `TechTag` declara columnas THEN incluye `slug: Mapped[str]` con UK [AC-4]
- WHEN `Niche` declara columnas THEN incluye `display_order: Mapped[int]` (no `position`) [AC-11]
- WHEN `TrackingEvent.__table_args__` THEN incluye `PrimaryKeyConstraint('created_at', 'visit_id', 'page_id')` [AC-10]

### `serverless/lambda/services/db/core/services/seed_service.py`

- WHEN seed lee `experiences/destacame-architect.yaml` con `start: "2022-08"` THEN `cv_experiences.started_on == date(2022, 8, 1)` [AC-2]
- WHEN seed lee YAML sin `end` THEN `cv_experiences.ended_on IS NULL` [AC-2]
- WHEN seed lee `awards/triple-alianza-lima-2020.yaml` con `awarded: "2020-08"` THEN `cv_awards.awarded_on == date(2020, 8, 1)` [AC-2]
- WHEN seed corre 2 veces idempotentemente THEN el row count no cambia (idempotencia preservada) [AC-12]
- WHEN seed inserta skill nuevo THEN `cv_skills.slug` es el slug derivado del name (`'Python'` -> `'python'`, `'Node.js'` -> `'node-js'`) [AC-4]
- WHEN seed inserta tech_tag nuevo THEN `tax_tech_tags.slug` similar [AC-4]
- WHEN seed inserta references THEN se persiste como `cv_endorsements` con `entity_type='endorsement'` en translations relacionadas [AC-9]

### Tests del shared kit (`shared/db/repository.py`, `shared/db/cv_repository.py`)

- WHEN query a profile THEN usa `cv_profiles` (verificable inspeccionando la SQL emitida con `echo=True` o `sqlalchemy.event`) [AC-1]
- WHEN query polimorfica a translations THEN usa `i18n_translations` [AC-1]

## 6.C — Typecheck

- `serverless tests --type=unit --lambda=<X>` corre con la `.venv` aislada del lambda; el `pyproject.toml` declara `pytest`, `pytest-mock`, `pytest-cov`.
- Mypy/ruff: el lint de Python verifica imports no rotos al cambiar paths de modelos. `python devtools/run.py serverless lint-deps --lambda=<X>` valida que el lambda declara explicitamente las deps que usa de shared.

## 6.D — E2E (Playwright) — N/A para esta spec

El rename no agrega flujos nuevos del usuario. El form `/contact` y el
pixel `/track` siguen funcionando identicos desde el browser. La suite
Playwright existente (`tests/feature/`) se ejecuta tal cual en la
bateria E2E final como regresion (`12-verificacion-e2e.md`).

## 6.E — Integration tests (pytest + Neon real)

Cada lambda corre `serverless tests --type=integration --lambda=<X>`
contra una branch Neon de prueba creada con `neonctl branches create
--name test-group-tables-by-domain --parent dev`.

### `services/db/tests/integration/`

- `test_migrate_renames_all_tables_e2e.py`: WHEN ejecuta `command=migrate` desde Alembic `d4e5f6a7b8c9` THEN la DB tiene exactamente las 37 tablas con prefijo correcto + `alembic_version` con `version_num` nuevo [AC-1]
- `test_migrate_downgrades_cleanly_e2e.py`: WHEN ejecuta `upgrade` y luego `downgrade -1` THEN la DB vuelve al estado `d4e5f6a7b8c9` exacto (nombres de tabla viejos restaurados) [AC-12]
- `test_seed_persists_dates_as_date_e2e.py`: WHEN ejecuta seed THEN cada fila de `cv_experiences` tiene `started_on` como tipo `date` (no string) [AC-2]
- `test_seed_skills_have_slugs_e2e.py`: WHEN ejecuta seed THEN `SELECT COUNT(*) FROM cv_skills WHERE slug IS NULL` retorna 0 [AC-4]
- `test_enum_endorsement_value_e2e.py`: WHEN ejecuta migrate THEN `pg_enum` tiene `'endorsement'` y NO tiene `'reference'` [AC-9]
- `test_tracking_events_pk_rejects_duplicate_e2e.py`: WHEN intenta INSERT 2 filas con la misma `(created_at, visit_id, page_id)` THEN PG retorna error 23505 [AC-10]
- `test_niches_display_order_e2e.py`: WHEN consulta `tax_niches.display_order` THEN existe la columna (no `position`) [AC-11]

### `services/stream_processor/tests/integration/`

- `test_writes_to_vis_tracking_events_e2e.py`: WHEN procesa un evento DDB Stream tipo INSERT en `TrackingTable` THEN aparece fila en `vis_tracking_events` con FK correcta a `vis_session_visits` y `tax_event_types` [AC-3]
- `test_writes_to_vis_contacts_e2e.py`: WHEN procesa un evento DDB Stream tipo INSERT en `ContactsTable` THEN aparece fila en `vis_contacts` con `session_id NOT NULL` [AC-5]

### `services/contact_form/tests/integration/`

- `test_post_contact_persists_to_vis_contacts_e2e.py`: WHEN POST a `/contact` con payload valido + Turnstile token mockeado THEN DynamoDB tiene la fila y (tras stream) Neon tiene fila en `vis_contacts` [AC-5]

### `services/tracking_pixel/tests/integration/`

- `test_post_track_persists_to_vis_tracking_e2e.py`: WHEN POST a `/track` THEN DynamoDB tiene fila y (tras stream) Neon tiene fila en `vis_tracking_events` [AC-3]

## 6.F — Tests existentes a actualizar

Lista exhaustiva en `04-archivos-afectados.md`. Resumen: ~30 tests
existentes referencian nombres viejos de tabla/columna y deben
actualizarse al nuevo naming. El `git grep -E '\b(profile|experiences|projects|contacts|sessions|tracking_events|niches|tech_tags|translations|event_types|skills|skill_categories|references|education)\b'` en `serverless/lambda/**/tests/` identifica los puntos.

## Coverage minimo

>= 80% per-file en archivos modificados o creados, verificado por
`serverless tests --type=coverage --lambda=<X>`. Esto es enforced por
el pre-push hook + por el commit de cierre (`12-verificacion-e2e.md`).

## Mocking guideline

- **Mockear**: HTTP a Cloudflare Turnstile, SES SendEmail, DynamoDB
  PutItem en unit tests, time/datetime cuando se necesite freeze.
- **NO mockear**: SQLAlchemy session, Alembic, repositorios propios,
  validators Pydantic propios. Para esos usar branch Neon real (en
  integration tests).

## Patron OBLIGATORIO — verificacion DB real post-feature en integration

Requisito explicito del usuario: **cada test integration de un lambda
debe terminar con una query directa a Neon que verifique que la data
persistio correctamente en las tablas con los nombres nuevos**. No
basta con `assert response.statusCode == 200` — hay que abrir conexion
psycopg y hacer SELECT.

Template:

```python
# services/<lambda>/tests/integration/test_X_e2e.py
import psycopg
import pytest
from uuid import uuid4


@pytest.fixture(scope='session')
def branch_db_url():
    """Connection string al branch Neon de prueba (e2e-verify)."""
    import os
    url = os.environ.get('DATABASE_URL')
    assert url, 'DATABASE_URL must point to the e2e-verify branch'
    return url


def test_lambda_persists_to_renamed_table_e2e(branch_db_url, lambda_invoker):
    # Arrange
    test_email = f"e2e-{uuid4()}@test.dev"
    payload = {'email': test_email, ...}

    # Act
    response = lambda_invoker.invoke('contact_form', payload)
    assert response['statusCode'] == 200

    # Assert -- VERIFICACION DB REAL (la clave del requisito)
    with psycopg.connect(branch_db_url) as conn:
        row = conn.execute(
            "SELECT id, email, session_id, status FROM vis_contacts WHERE email = %s",
            (test_email,)
        ).fetchone()
    assert row is not None, f"no row found in vis_contacts for {test_email}"
    assert row[1] == test_email
    assert row[2] is not None, "session_id must be NOT NULL (AC-5)"
    assert row[3] == 'new', "default status"


def test_lambda_data_in_partition_e2e(branch_db_url, lambda_invoker):
    # Verificar que las inserciones llegan a la particion default
    visit_id = uuid4()
    page_id = uuid4()
    response = lambda_invoker.invoke('tracking_pixel', {...})
    assert response['statusCode'] == 200

    with psycopg.connect(branch_db_url) as conn:
        # Query a la TABLA (no la particion) — PG resuelve automaticamente
        row = conn.execute(
            "SELECT visit_id, page_id, event_type_id FROM vis_tracking_events "
            "WHERE visit_id = %s AND page_id = %s",
            (visit_id, page_id)
        ).fetchone()
    assert row is not None
```

### Que verificar por cada lambda

| Lambda | Query post-feature minima |
|---|---|
| `contact_form` | `SELECT id, email, session_id FROM vis_contacts WHERE email=<test>` |
| `tracking_pixel` | `SELECT visit_id, page_id FROM vis_tracking_events WHERE session_id=<test>` + `SELECT session_id FROM vis_sessions WHERE session_id=<test>` + `SELECT visit_id FROM vis_session_visits WHERE session_id=<test>` |
| `stream_processor` (process contact stream) | mismo SELECT a `vis_contacts` |
| `stream_processor` (process tracking stream) | mismo SELECT a `vis_tracking_events` |
| `db` (seed) | `SELECT count(*) FROM cv_profiles, cv_experiences, cv_endorsements, cv_skills, tax_niches, i18n_translations` |
| `cv` (si existe, GET /cv?action=profile) | `SELECT * FROM cv_profiles` y comparar con response |

### Por que ESTA verificacion atrapa errores que el unit no atrapa

- Detecta **drift entre nombre del modelo y nombre real de la DB**
  (clase apuntaria a `vis_contacts` pero la DB sigue con `contacts` si
  la migracion fallo silenciosamente).
- Detecta **caracteristicas perdidas en el rename**: NOT NULL, default
  values, FKs, triggers.
- Detecta **fallas de cascade**: si la migracion no preservo el
  `ON DELETE CASCADE`, el FK queda sin cascade y un cleanup de tests
  falla intermitentemente.
- Detecta **diferencias de tipo**: el modelo declara `started_on: date`
  pero la DB todavia tiene `varchar(7)` (la migracion no convirtio).

### Fixture compartida para branch Neon de prueba

`serverless/lambda/shared/tests/_fixtures/branch_db.py` (nuevo):

```python
import pytest
import subprocess
import os


@pytest.fixture(scope='session')
def neon_test_branch():
    """Crea branch Neon e2e-<pid>, expone DATABASE_URL, cleanup al final."""
    branch_name = f"e2e-{os.getpid()}"
    subprocess.run(['neonctl', 'branches', 'create',
                    '--name', branch_name,
                    '--parent', 'dev'], check=True)
    url = subprocess.check_output(
        ['neonctl', 'connection-string', branch_name,
         '--role-name', 'neondb_owner']
    ).decode().strip()
    yield url
    subprocess.run(['neonctl', 'branches', 'delete', branch_name], check=True)
```

Cada lambda importa esta fixture en su `conftest.py` de integration.
