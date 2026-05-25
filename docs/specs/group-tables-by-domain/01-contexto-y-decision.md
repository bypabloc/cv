# 01 — Contexto, Solucion y Criterios de Aceptacion

[README](README.md) | **01-contexto** | [02-diagrama-er](02-diagrama-er.md)

## 1. Contexto / Problema

El schema unificado de Neon (37 tablas tras la migration `d4e5f6a7b8c9`)
mezcla tablas de 4 dominios distintos sin separador visual: datos del CV
(profile, experiences, projects, certificates...), tracking del visitante
(contacts, sessions, tracking_events), taxonomia compartida (niches,
tech_tags, event_types) e internacionalizacion (translations). Al
consultar `\dt` en `psql` o `information_schema.tables` aparecen las 37
tablas en un solo bloque alfabetico, dificultando navegar el schema y
entender que entidades pertenecen a que subsistema.

Ademas, hay inconsistencias acumuladas en nombres de columnas, tipos y
estructura que se acarrean desde la migration inicial
`81c2cc51db34_init_unified_schema`:

1. **Fechas como `VARCHAR`** con CHECK `YYYY-MM`
   (`experiences.start_ym`, `awards.awarded_ym`) o `VARCHAR(16)` sin
   CHECK (`education.start_year`) en vez del tipo `DATE` estandar.
2. **`tech_tags` y `skills`** solo tienen `name UNIQUE` sin `slug`,
   inconsistente con el resto del CV donde cada entidad tiene
   `slug VARCHAR(120) UNIQUE` estable.
3. **`tracking_events` sin PK fisica** — declarada PK compuesta en el
   ORM pero NO en PG; impide `INSERT ... ON CONFLICT` e idempotencia.
4. **`references` es palabra reservada SQL**, requiere quotes en
   queries ad-hoc (`SELECT * FROM "references"`).
5. **`niches.position` vs `niche_priorities.priority`** son dos
   columnas con nombre similar y semantica distinta (orden visual vs
   peso por entidad), faciles de confundir.
6. **`education` y `profile` son singulares** mientras el resto del
   schema es plural — convencion inconsistente.

### Hallazgos de exploracion

- **Drift entre branches Neon**: dev tiene el schema unificado al dia
  (Alembic `d4e5f6a7b8c9`, 37 tablas + alembic_version). stage y
  production tienen el schema viejo del runner SQL archivado (7 tablas,
  sin Alembic).
- **Data en dev**: 372 filas en translations, 99 skills, 9 experiences,
  4 projects, 36 niche_priorities, 2 sessions, 7 tracking_events
  (default partition).
- **El usuario confirmo que la data de stage/prod se descarta** — solo
  esta probando, va a rehacer toda la data tras el rename.

## 2. Solucion Propuesta

Aplicar UN solo PR `feature/group-tables-by-domain -> dev` con UNA
migracion Alembic que renombra las 37 tablas con prefijos
`cv_`/`vis_`/`tax_`/`i18n_`, normaliza columnas inconsistentes,
reorganiza los modelos SQLAlchemy en subcarpetas por dominio, actualiza
las 4 Lambdas downstream + el seeder, y al mergear a dev/stage/prod
provisiona stage y prod desde cero (destroy + recreate).

### Decisiones clave

- **Decision 1**: prefijo en `__tablename__` (NO PG schemas). Razon:
  cero overhead, sin cambios en `search_path`, grep-friendly,
  compatible con Alembic estandar.
- **Decision 2**: clases Python conservan nombre (`Profile`, `Contact`,
  `Niche`); cambia solo `__tablename__` y el path del archivo. Razon:
  cero refactor de los call-sites (`from shared.db.models.cv import
  Profile` en vez de `from ... import Profile`).
- **Decision 3**: una migracion Alembic atomica con todos los renames.
  Razon: minimiza ventana de inconsistencia, los Lambdas se redeployan
  en el mismo CI run despues de `migrate-db`.
- **Decision 4**: stage y prod se rehacen desde cero. Razon: el
  usuario confirmo que la data es de prueba, descartable. Simplifica
  el plan eliminando una "Fase 0" de migrar stage/prod al schema
  unificado primero.
- **Decision 5**: `DATE` en DB + seeder convierte YAML `2024-01` a
  `date(2024, 1, 1)`. Razon: los YAMLs siguen legibles para CV; la DB
  gana operadores nativos (ORDER BY, EXTRACT, comparaciones); no
  requiere migrar 25+ archivos YAML.
- **Decision 6**: `name` directo en `cv_skills` y `tax_tech_tags`
  (NO movido a `i18n_translations`). Razon: son identificadores
  tecnicos sin localizacion (Python, React, PostgreSQL), idem en es/en.
  Mover a translations seria 198 filas extra de zero-value y un join
  en cada query.

## 3. Criterios de Aceptacion

Formato BDD (Given/When/Then). Cada AC es la fuente de verdad — los
tests del plan los referencian.

### AC-1 — Tablas prefijadas en dev

**Given** branch `dev` Neon con Alembic en `d4e5f6a7b8c9`,
**When** `serverless run --stage=dev --lambda=db --event=events/migrate.json`
ejecuta la migracion nueva,
**Then** `SELECT table_name FROM information_schema.tables WHERE
table_schema = 'public'` retorna 37 tablas todas con prefijo
`cv_`/`vis_`/`tax_`/`i18n_` + `alembic_version` + 1 particion default.

### AC-2 — Conversion de fecha YAML a DATE

**Given** seed YAML `experiences/destacame-architect.yaml` con
`start: "2022-08"`,
**When** `serverless run --stage=dev --lambda=db --event=events/seed.json`
ejecuta el seed,
**Then** `SELECT started_on FROM cv_experiences WHERE slug =
'destacame-architect'` retorna `date(2022, 8, 1)` (tipo `date`, no
`varchar`).

### AC-3 — stream_processor escribe a tablas renombradas

**Given** schema dev renombrado + Lambdas redeployadas con imports
actualizados,
**When** un evento `cta_click` llega a DynamoDB Stream y el
`stream_processor` lo replica,
**Then** aparece una fila en `vis_tracking_events` con FK
`event_type_id` a `tax_event_types`.

### AC-4 — slugs en skills y tech_tags

**Given** seed ejecutado en dev post-migracion,
**When** `SELECT slug, name FROM cv_skills LIMIT 5`,
**Then** todas las filas tienen `slug NOT NULL` (kebab-case ASCII) y
`name NOT NULL` (display casing). Idem `tax_tech_tags`.

### AC-5 — contact form sigue funcionando

**Given** schema dev renombrado + `contact_form` Lambda redeployada,
**When** POST a `/contact` con payload valido + Turnstile token,
**Then** aparece fila en `vis_contacts` con `session_id NOT NULL` (FK
a `vis_sessions`) y status `new`.

### AC-6 — stage provisionado desde cero

**Given** PR mergeado a `stage`,
**When** workflow `deploy-backend.yml` corre con stage,
**Then** la branch Neon `stage` queda con schema renombrado completo
(37 tablas + alembic_version), data vieja descartada, seed re-ejecutado.

### AC-7 — prod provisionado desde cero

**Given** PR mergeado a `main`,
**When** workflow `deploy-backend.yml` corre con prod,
**Then** branch Neon `production` queda con schema renombrado completo,
data vieja descartada, seed re-ejecutado.

### AC-8 — Imports Python actualizados

**Given** los 4 Lambdas (`db`, `stream_processor`, `contact_form`,
`tracking_pixel`) redeployados,
**When** `python -m compileall -q serverless/lambda/`,
**Then** zero `ModuleNotFoundError` y zero `ImportError` (todos los
imports apuntan a las subcarpetas nuevas: `shared.db.models.cv`,
`shared.db.models.visitor`, etc.).

### AC-9 — ENUM entity_type incluye 'endorsement'

**Given** migracion ejecutada con `ALTER TYPE entity_type RENAME VALUE
'reference' TO 'endorsement'`,
**When** `SELECT enumlabel FROM pg_enum WHERE enumtypid =
(SELECT oid FROM pg_type WHERE typname = 'entity_type')`,
**Then** el resultado contiene `'endorsement'` y NO contiene
`'reference'`.

### AC-10 — PK fisica en vis_tracking_events

**Given** schema dev renombrado con PK compuesta `(created_at,
visit_id, page_id)` en `vis_tracking_events`,
**When** se intenta `INSERT INTO vis_tracking_events (...) VALUES
(...)` con la misma tripla,
**Then** PG retorna `duplicate key value violates unique constraint
"vis_tracking_events_pkey"` (error 23505).

### AC-11 — niches.display_order

**Given** schema dev renombrado,
**When** `SELECT column_name FROM information_schema.columns WHERE
table_name = 'tax_niches'`,
**Then** existe `display_order` y NO existe `position`.

### AC-12 — tests verdes

**Given** todo el codigo del plan implementado,
**When** `serverless tests --type=unit --lambda=db && serverless tests
--type=unit --lambda=stream_processor && serverless tests --type=unit
--lambda=contact_form && serverless tests --type=unit
--lambda=tracking_pixel && serverless tests --type=unit --shared`,
**Then** zero tests rojos, coverage >= 80% per-file en archivos
modificados.
