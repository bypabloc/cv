# Plan: Unificacion del schema PostgreSQL en SQLAlchemy + Alembic

> Consolidar TODO el schema PostgreSQL del portfolio (las tablas del CV de
> `db/cv/` + las del backend serverless de `serverless/migrations/*.sql`) en
> un unico set de modelos SQLAlchemy 2.x, gestionado por un solo Alembic. Las
> Lambdas usan el ORM (Session + objetos). Una Lambda `db` nueva gestiona las
> migraciones, con estructura factory escalable por payload.

## 1. Contexto / Problema

Hoy el schema PostgreSQL del portfolio esta partido en DOS sistemas:

| Dominio | Tablas | Como se define hoy |
|---------|--------|--------------------|
| Backend serverless | `contacts`, `tracking_events` (+`tracking_events_default`), `processed_stream_events`, `event_types`, `schema_migrations` | 11 archivos `.sql` crudos en `serverless/migrations/` + runner `migrate.py` |
| CV | 31 tablas (`experiences`, `projects`, `translations`, ...) | Modelos SQLAlchemy en `db/cv/` + Alembic (recien creado) |

El `stream_processor` consume Neon con `psycopg` crudo (`pg_writer.py`, SQL
strings). No hay una fuente unica de verdad del schema: el backend lo define
en SQL, el CV en SQLAlchemy.

El usuario quiere: (a) UNA sola fuente de verdad — modelos SQLAlchemy para
TODO; (b) las Lambdas usando el ORM; (c) una Lambda `db` que gestione las
migraciones con comandos (`migrate`, `show-migrations`, ...).

### Hallazgos de exploracion

- Backend: 6 tablas. `tracking_events` esta **particionada por RANGE
  (created_at)** con una particion default; tiene una **FK en tabla
  particionada** (`event_type_id -> event_types`). Usa la extension
  `citext` (`contacts.email`), tipos `INET`, `CHAR(2)`, `JSONB`, indices
  GIN/BRIN/parciales. `event_types` es un catalogo con seed.
  `schema_migrations` es el log del runner viejo — se reemplaza por
  `alembic_version`.
- `contact_form` y `tracking_pixel` escriben a **DynamoDB** (boto3), NO a
  Neon. Solo el `stream_processor` toca Neon (consume DynamoDB Streams).
  -> el ORM en runtime aplica primariamente al `stream_processor`.
- `db/cv/` ya tiene 31 modelos + Alembic + seed funcionando (32 tests
  verdes). Se ABSORBE: sus modelos se mueven al modulo unificado.
- Empaquetado SAM: `CodeUri: src/` — todo lo que se comparta entre Lambdas
  va en `serverless/src/common/`. Deps pesadas van en Lambda Layers
  (`CommonLayer`, `PostgresLayer` ya existen).
- `devtools/run.py` es el patron factory de referencia: entrypoint unico +
  plugin loader dinamico por argumento posicional.

### Decisiones del usuario

1. **Reescribir las 11 `.sql` como migraciones Alembic desde cero** — el
   schema resultante debe ser equivalente al que hay en prod.
2. **ORM completo** — las Lambdas usan Session + objetos mapeados.
3. **Lambda `db`** con estructura factory (como `devtools/run.py`), escala
   por el payload de entrada: `{"command": "migrate"}`,
   `{"command": "show-migrations"}`, etc.
4. **Un unico set de modelos** CV + backend; `db/cv/` se absorbe y
   desaparece.

## 2. Solucion Propuesta

Crear `serverless/src/common/db/` como el modulo unico de schema: modelos
SQLAlchemy 2.x de las **37 tablas** (6 backend + 31 CV), un Alembic unico,
y la utilidad de Session/engine. Una Lambda `db` nueva (factory por comando)
corre las migraciones. El `stream_processor` se reescribe a ORM. `db/cv/` se
elimina (su contenido se absorbe).

### 2.1. Modulo unificado `serverless/src/common/db/`

Todas las tablas pertenecen a la MISMA base de datos — no hay sub-namespaces
por dominio. Los modelos viven planos en `models/`, agrupados por cohesion
de tabla (que tablas se referencian entre si), no por su origen historico.

```text
serverless/src/common/db/
├── __init__.py              # re-exporta Base + engine/session + modelos
├── base.py                  # DeclarativeBase + mixins (uuid pk, timestamps)
├── enums.py                 # todos los ENUMs nativos
├── session.py               # engine + sessionmaker, conn cacheada module-scope
├── models/
│   ├── __init__.py          # re-exporta los 37 modelos, planos
│   ├── contact.py           # contacts
│   ├── tracking.py          # tracking_events (particionada) + default + event_types
│   ├── stream.py            # processed_stream_events
│   ├── profile.py           # profile + profile_stats
│   ├── catalog.py           # niches + skills + tech_tags
│   ├── experience.py        # experiences + experience_bullets
│   ├── project.py           # projects + project_case_studies + project_metrics
│   ├── cv_entities.py       # certificates, awards, education, references,
│   │                        #   languages, skill_categories, publications
│   ├── junctions.py         # las 12 tablas de union N:M
│   └── translations.py      # translations + niche_priorities
└── alembic/
    ├── env.py               # target_metadata = Base.metadata (las 37 tablas)
    ├── alembic.ini
    └── versions/            # migraciones reescritas + el trigger
```

> Un solo `Base.metadata` cubre las 37 tablas. Un solo Alembic, una sola
> tabla `alembic_version`. `schema_migrations` (el log del runner viejo) se
> elimina. Para quien importa: `from common.db.models import Contact,
> Experience` — sin jerarquia de dominio, una sola DB.

### 2.2. Lambda `db` — factory por payload

```text
serverless/src/db/
├── __init__.py
├── handler.py               # lambda_handler: lee command del payload, dispatch
├── commands/                # factory: un archivo por comando (escalable)
│   ├── __init__.py          # registry {nombre: funcion}
│   ├── migrate.py           # alembic upgrade head
│   ├── show_migrations.py   # alembic history + current
│   ├── downgrade.py         # alembic downgrade <target> (requiere confirm)
│   ├── current.py           # revision aplicada actualmente
│   └── stamp.py             # alembic stamp (marca sin ejecutar)
└── requirements.txt
```

Contrato del payload: `{"command": "migrate", "args": {...}}`. El
`handler.py` valida `command`, busca la funcion en el registry y la invoca
— mismo patron que `devtools/run.py` (plugin loader), pero el "argumento"
es el payload en vez de `sys.argv`.

### 2.3. ORM en runtime — `stream_processor`

`pg_writer.py` (141 lineas, SQL crudo) se reescribe usando el ORM:
`session.add(Contact(...))`, `session.execute(select(...))`. La conexion
sigue cacheada a module-scope (cold start). `transformers.py` y
`handler.py` se ajustan para producir/consumir objetos mapeados.

### 2.4. Layers

SQLAlchemy + Alembic son deps nuevas. Decision: **`PostgresLayer` absorbe
SQLAlchemy** (ya tiene `psycopg`; las Lambdas que tocan Neon son las mismas
que necesitan el ORM). **Alembic va en un Layer aparte `MigrationLayer`**
que SOLO usa la Lambda `db` — Alembic no se necesita en runtime de
`stream_processor`, meterlo en `PostgresLayer` inflaria su cold start.

### Decisiones clave

- **Decision 1: baseline-by-rewrite, validado contra prod** — las 11 `.sql`
  se traducen a UNA migracion Alembic inicial que produce el schema
  equivalente al actual. Para garantizar cero drift: se compara el schema
  generado por Alembic contra el schema real de prod (introspeccion). En
  prod NO se re-crea nada: se hace `alembic stamp head` (marca el estado
  como ya migrado) — los datos de `contacts`/`tracking_events` NO se tocan.
  En dev/branches efimeros si se corre `upgrade` real desde cero.

- **Decision 2: un solo `Base.metadata`, modelos planos** — todas las tablas
  pertenecen a la misma DB; NO hay sub-carpetas por dominio (`backend/` /
  `cv/`). Los modelos viven planos en `models/`, agrupados por cohesion de
  tabla. Un Alembic, un `alembic_version`. Quien importa lo hace plano:
  `from common.db.models import Contact, Experience`.

- **Decision 3: `tracking_events` particionada — declarativa parcial** —
  Alembic/SQLAlchemy no autogeneran `PARTITION BY RANGE` ni la particion
  default. El modelo declara las columnas; el `PARTITION BY` y la particion
  default se agregan como `op.execute()` explicito en la migracion (igual
  que el trigger del CV). Esto se revisa a mano — es la parte de mayor
  cuidado del plan.

- **Decision 4: la Lambda `db` reemplaza al runner `migrate.py`** — el
  comando `serverless db-migrate` de devtools deja de invocar `migrate.py`
  y pasa a invocar la Lambda `db` (o corre alembic directo en CI). El
  runner `serverless/scripts/migrate.py` y los 11 `.sql` se archivan.

- **Decision 5: `db/cv/` se elimina** — su contenido (modelos, seed) se
  mueve a `serverless/src/common/db/`. El seed del CV pasa a ser un comando
  mas de la Lambda `db` (`{"command": "seed-cv"}`) o un script de devtools.
  El diagrama ER se actualiza para reflejar las 37 tablas.

- **Decision 6: ORM completo solo donde se usa** — `stream_processor` se
  reescribe a ORM. `contact_form`/`tracking_pixel` NO cambian (escriben a
  DynamoDB, no a Neon). El "ORM completo" aplica al codigo que toca Neon.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given los modelos unificados, When se corre `alembic upgrade
  head` sobre una DB PostgreSQL 18 limpia, Then se crean las 37 tablas
  (6 backend + 31 CV) sin error.
- **AC-2**: Given el schema generado por Alembic y el schema real de prod,
  When se comparan por introspeccion (tablas, columnas, tipos, indices,
  constraints), Then son equivalentes — cero drift.
- **AC-3**: Given `tracking_events`, When se inspecciona, Then esta
  particionada por RANGE(created_at) y tiene `tracking_events_default`.
- **AC-4**: Given la Lambda `db` invocada con `{"command":"migrate"}`,
  Then aplica las migraciones pendientes y responde el estado final.
- **AC-5**: Given la Lambda `db` con `{"command":"show-migrations"}`, Then
  responde el historial + la revision actual.
- **AC-6**: Given la Lambda `db` con un `command` desconocido, Then
  responde un error claro sin ejecutar nada.
- **AC-7**: Given el `stream_processor` reescrito a ORM, When procesa un
  DynamoDB Stream record, Then inserta en `contacts`/`tracking_events` via
  Session con el mismo resultado que `pg_writer.py` (idempotencia incluida).
- **AC-8**: Given prod con datos en `contacts`/`tracking_events`, When se
  adopta Alembic (`stamp head`), Then los datos quedan intactos y
  `alembic_version` registra la revision baseline.
- **AC-9**: Given `event_types` (catalogo con seed), When se aplica la
  migracion, Then el catalogo queda sembrado igual que las migraciones
  006+008 actuales.
- **AC-10**: Given el modulo `common/db/`, When las 3 Lambdas se empaquetan,
  Then `stream_processor` y `db` resuelven los imports; el bundle de
  `contact_form`/`tracking_pixel` no crece con SQLAlchemy innecesario.

## 4. Diagrama de Flujo (Antes y Despues)

### Antes

```text
serverless/migrations/*.sql  ──>  migrate.py  ──>  Neon (schema backend)
db/cv/models/ (SQLAlchemy)   ──>  alembic     ──>  Neon (schema CV)
stream_processor ── pg_writer.py (psycopg crudo) ──> Neon
```

### Despues

```text
serverless/src/common/db/models/ (SQLAlchemy, 37 tablas)
        │  (unica fuente de verdad)
        ├──> alembic ──> Lambda `db` (command: migrate) ──> Neon
        └──> stream_processor (ORM Session) ──> Neon
```

## 5. Diagrama ER

Aplica: se actualiza `docs/diagrams/cv-er.mmd` -> renombrar a
`db-er.mmd` con las 37 tablas (31 CV ya diagramadas + 6 backend nuevas:
`contacts`, `tracking_events`, `tracking_events_default`,
`processed_stream_events`, `event_types`). El detalle de columnas de las
6 nuevas se toma de `serverless/migrations/001..010`.

## 6. Tests Requeridos

### 6.A. Migraciones (Alembic)
- `alembic upgrade head` sobre branch Neon limpio crea las 37 tablas [AC-1].
- `alembic downgrade base` revierte limpio.

### 6.B. Unit / integration tests (pytest)
- `test_schema_parity_with_prod` — introspeccion: el schema Alembic ==
  schema de prod [AC-2].
- `test_tracking_events_partitioned` — `tracking_events` particionada [AC-3].
- `test_event_types_seeded` — el catalogo sembrado [AC-9].
- `test_db_lambda_migrate` / `test_db_lambda_show` / `test_db_lambda_unknown
  _command` — la Lambda `db` por payload [AC-4, AC-5, AC-6].
- `test_stream_processor_orm_insert` — el stream_processor ORM inserta
  igual que antes, idempotencia incluida [AC-7].
- Tests del CV migrados desde `db/cv/tests/` (siguen verdes).
- Coverage >= 80% per-file en el codigo nuevo.

### 6.C. Typecheck / lint
- Ruff sobre `serverless/src/common/db/` + `serverless/src/db/`.
- Los modelos SQLAlchemy 2.x tipados (`Mapped[...]`).

### 6.D. E2E
- Smoke test del `stream_processor` reescrito contra un branch Neon (el
  `smoke_test.sh` existente se adapta).

## 7. Archivos Afectados

### Crear
- `serverless/src/common/db/` — modulo unificado (base, enums, session,
  `models/*` planos, `alembic/`)
  - Verificar: `python -c "from common.db import Base; ..."`
  - Verificar: `alembic upgrade head` sobre branch Neon limpio
- `serverless/src/db/` — Lambda `db` (handler factory + `commands/*`)
  - Verificar: invoke local con payloads de cada comando
- `serverless/layers/migration_python/requirements.txt` — Layer Alembic
- `serverless/src/db/tests/`, tests de schema parity
- `docs/diagrams/db-er.mmd` — ER de las 37 tablas

### Modificar
- `serverless/template.yaml` — agregar la Lambda `db` + `MigrationLayer`;
  SQLAlchemy entra a `PostgresLayer`
- `serverless/src/stream_processor/pg_writer.py` + `handler.py` +
  `transformers.py` — reescritos a ORM
- `serverless/layers/postgres_python/requirements.txt` — agregar SQLAlchemy
- `devtools/serverless/database.py` — `db-migrate` pasa a invocar la Lambda
  `db` (o alembic directo en CI)
- `CLAUDE.md`, `.claude/rules/neon-management.md` — documentar el modelo
  unificado y la Lambda `db`

### Eliminar / archivar
- `db/cv/` completo — absorbido por `serverless/src/common/db/`
- `serverless/migrations/*.sql` (11 archivos) + `serverless/scripts/migrate.py`
  — archivados (su contenido se reescribio a Alembic)
- `serverless/migrations/005` crea `schema_migrations` — reemplazada por
  `alembic_version`

## 8. Descomposicion para Paralelizacion

Large (40+ archivos, alto riesgo). Implementacion secuencial por fases con
checkpoint de verificacion entre cada una:

1. **Fase A** — modulo `common/db/` con modelos backend + CV unificados;
   `alembic upgrade head` verde sobre branch limpio (AC-1, AC-3).
2. **Fase B** — validar parity contra prod (AC-2); definir el `stamp` de
   prod (AC-8).
3. **Fase C** — Lambda `db` factory + Layer Alembic (AC-4, AC-5, AC-6).
4. **Fase D** — reescritura del `stream_processor` a ORM (AC-7) + smoke.
5. **Fase E** — `template.yaml`, devtools, docs; eliminar `db/cv/` y los
   `.sql`; ER actualizado.

No se paraleliza con worktrees: `Base.metadata` es un punto unico y las
fases dependen en cadena.

## 8.bis. Hallazgos de la Fase B (parity contra prod)

Comparacion del schema generado por Alembic (branch limpio) contra el
schema real de prod (`br-misty-math-akuyhn9c`), tablas del backend:

- **Columnas** — IDENTICAS tras dos correcciones a los modelos: `country`
  paso de `VARCHAR(2)` a `CHAR(2)` (prod usa CHAR fijo); `contacts.session_id`
  reordenada al final (la migracion 010 la agrego con ALTER TABLE).
- **Indices** — los 15 `idx_*` del backend coinciden exactamente.
- **CHECK constraints** — equivalentes en logica (mismos valores permitidos).
- **Drift cosmetico ACEPTADO**: los nombres de constraints PK/UNIQUE/CHECK
  difieren — Alembic usa la naming convention (`pk_*`/`uq_*`/`ck_*`), prod
  usa los defaults de PG (`*_pkey`/`*_key`/`*_check`). NO afecta
  funcionalidad. Como en prod se hace `stamp` (no `upgrade` que recree),
  prod conserva sus nombres; solo un branch nuevo tendria los de Alembic.
- **Tablas huerfanas en prod**: `daily_metrics` y `tracking_daily_aggregates`
  existen en prod pero NO en ninguna de las 11 migraciones `.sql` ni en los
  modelos (restos de specs descartadas). El `include_name` del `env.py` las
  ignora — Alembic no las toca ni las borra. Quedan fuera del schema
  gestionado; limpiarlas es una decision aparte del owner.

Conclusion: el schema unificado es equivalente al de prod. En prod se
aplica `alembic stamp head` (marca la revision baseline sin tocar datos);
el `upgrade` real solo corre en branches/dev nuevos.

## 9. Validacion y Definition of Done

### Pre-implementacion
- [ ] AC-1..AC-10 referenciados por tests
- [ ] Branch Neon efimero disponible para migraciones de prueba
- [ ] Snapshot del schema de prod capturado (para el test de parity)
- [ ] Confirmado: el `stamp` de prod NO recrea tablas (datos intactos)

### Definition of Done
- [ ] `alembic upgrade head` + `downgrade base` verdes en branch efimero
- [ ] Test de parity schema-vs-prod pasa (cero drift)
- [ ] La Lambda `db` responde a `migrate` / `show-migrations` / comando
      invalido
- [ ] `stream_processor` reescrito a ORM; smoke test verde
- [ ] Todos los AC con test que los cubre y pasa; coverage >= 80%
- [ ] Ruff limpio sobre el codigo nuevo
- [ ] `db/cv/` eliminado; `serverless/migrations/*.sql` archivados
- [ ] `docs/diagrams/db-er.mmd` refleja las 37 tablas
- [ ] CLAUDE.md + neon-management.md actualizados
- [ ] El branch Neon de prueba se elimina al cerrar

## 10. Riesgos

| Riesgo | Mitigacion |
|--------|-----------|
| El schema Alembic no es identico al de prod (drift) | Test de parity por introspeccion ANTES de tocar prod; en prod solo `stamp`, nunca `upgrade` que recree |
| `tracking_events` particionada mal modelada | `PARTITION BY` via `op.execute()` explicito + test que verifica la particion; revision manual |
| ORM agranda el cold start del `stream_processor` | SQLAlchemy en `PostgresLayer`; medir cold start antes/despues; Session ligera, sin lazy-loading innecesario |
| La Lambda `db` con permisos de migracion es sensible | IAM scoped; invocacion restringida (no API Gateway publica); requiere confirm para `downgrade` |
| Perder el historial de los 11 `.sql` | Se archivan, no se borran (referencia historica) |

## 11. Re-scope (2026-05-19) — sin Layers, `_shared`, Lambda API

Durante la Fase E el usuario amplio el alcance. Decisiones nuevas:

### 11.1 — Sin Lambda Layers

Se ELIMINA el concepto de `serverless/layers/*`. Todo el codigo y las
dependencias compartidas se manejan dentro de `serverless/src/`. El
empaquetado SAM (`CodeUri: src/`) lleva las deps via `requirements.txt`
por Lambda. Razon: simplicidad — un solo arbol de codigo, sin la friccion
de mantener Layers y su build `--use-container`.

### 11.2 — `common/` se renombra a `_shared/`

`serverless/src/common/` pasa a `serverless/src/_shared/` — codigo puro
reciclable entre Lambdas (db, util, cors, rate_limit, cache, ...). El
prefijo `_` marca "interno, compartido, no es una Lambda".

### 11.3 — Nueva Lambda `api` (commit aparte, NO en este)

Una Lambda `api` con la MISMA estructura factory que `db`:

- Acciones: `get` con subacciones `cv` (= `curriculum`) y `elements`.
- Argumentos dinamicos de filtrado: `language` (es/en), y mas a futuro.
- Expone los datos del CV (hoy en los YAML de `packages/content/`) y los
  labels i18n (`elements`) — en JSON con la MISMA forma que los YAML
  actuales, para que `packages/content` cambie de fuente con minimo
  impacto.
- Detras de **API Gateway REST**. Las apps Astro la consultan en
  build-time / runtime.
- **Auth — HMAC firmado** (el patron "public genera, private contrasta"
  que pidio el usuario es exactamente HMAC):
  - La app tiene una clave publica (`key_id` + secreto compartido) en
    `docker/env/client/*`.
  - El server tiene el secreto privado en `docker/env/server/*` / SSM.
  - La app firma cada request: `HMAC-SHA256(secreto, timestamp + path)`,
    lo manda en un header. El server recomputa y compara. Ventana de
    timestamp corta (±5 min) contra replay. El secreto nunca viaja.
  - Alternativas validas: JWT HS256 de vida corta; API Key nativa de API
    Gateway (estatica — descartada por no ser dinamica).

### 11.4 — Seed del CV (commit aparte, NO en este)

El seed (`db/cv/seed/seed_from_yaml.py`) migra como comando de la Lambda
`db` (`{"command": "seed-cv"}`). Requiere empaquetar los YAML del CV con
la Lambda. Se hace junto con la Lambda `api`.

### 11.5 — Alcance de ESTE commit

Cierra: schema unificado + Lambda `db` (migraciones) + `stream_processor`
ORM + eliminar Layers + rename `common` -> `_shared`. NO incluye la
Lambda `api` ni el seed — van en un commit/plan siguiente.

`db/cv/` se conserva por ahora (solo `db/cv/seed/` tiene logica aun no
migrada). Los `.sql` de `serverless/migrations/` se archivan.
