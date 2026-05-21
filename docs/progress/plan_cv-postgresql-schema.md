# Plan: Migracion del CV de YAML a PostgreSQL (schema relacional 3NF)

> Modelar las 9 entidades del CV (hoy en YAML) como un schema PostgreSQL
> normalizado a 3NF, con tabla de traducciones, niches/skills/tags
> normalizados, migraciones via SQLAlchemy + Alembic, y un seed con la data
> real. La DB pasa a ser la fuente de verdad; el frontend Astro la consume
> en build-time.

## 1. Contexto / Problema

La data del CV de Pablo Contreras vive hoy en `packages/content/src/data/`
como archivos YAML (1 por entry), cargados por el frontend Astro en
build-time via `loadYamlEntries` + Zod. Entidades actuales:

| Entidad | Entries | Campos clave |
|---|---|---|
| profile | 1 (singleton) | headline, summary, contacts, stats — bilingue |
| experiences | 9 | role, company, fechas, responsibilities[], achievements[], skills, seniority |
| projects | 6 | name, summary, stack[], caseStudyDetailed, metrics{}, projectType, status |
| skills | 10 categorias | name, skills[] (array de strings), kind (technical/soft) |
| certificates | 11 | title, issuer, date, url |
| awards | 2 | title, issuer, date, motivation |
| education | 3 | institution, degree, fechas, description |
| references | 10 | name, role, relation, company, linkedin |
| languages | 2 | name, level |
| publications | 0 (vacia, schema existe) | title, platform, url, date, summary |

Patrones transversales: casi todas tienen `slug`, `niches[]` (subconjunto de
5 niches) y campos bilingues `{es, en}`. `experiences`/`projects` tienen
`priority` (peso por niche para ordenar). `projects` embebe estructuras
(`caseStudyDetailed`, `metrics`).

El usuario quiere migrar esta data a PostgreSQL relacional como fuente de
verdad editable, manteniendo el sitio estatico.

### Hallazgos de exploracion

- El backend serverless ya usa Neon PostgreSQL 18 (tablas `contacts`,
  `tracking_events` en schema `public`) con un runner SQL versionado propio
  (`serverless/migrations/NNN_*.sql` + `migrate.py`).
- Decision del usuario: las tablas del CV van al **mismo Neon, mismo schema
  `public`**; migraciones via **SQLAlchemy + Alembic** (nuevo, autogenerate);
  campos bilingues en **tabla de traducciones**; arrays en **3NF completo**;
  niche+priority con **union simple + tabla de priority aparte**; frontend
  consume la DB en **build-time** (sigue estatico).
- Esto introduce un 2do sistema de migracion (Alembic) junto al runner SQL
  del backend. Se asume deliberadamente — ver Decision 6.

## 2. Solucion Propuesta

Un schema PostgreSQL 18 normalizado a 3NF con ~24 tablas: 9 de entidades, 1
de catalogo (`niches`), 2 de vocabularios compartidos (`skills`,
`tech_tags`), tablas de union para cada relacion N:M, 1 tabla generica de
traducciones y 1 tabla generica de priority por niche.

### Estrategia de modelado

**a) Entidades.** Una tabla por entidad del CV. Los campos NO bilingues y NO
multivaluados van como columnas nativas (fechas, urls, enums, flags). PK
`id uuid` (UUIDv7, PostgreSQL 18 trae `uuidv7()` nativo) + `slug` con
`UNIQUE` para el match con los YAML/legacy.

**b) Traducciones (tabla unica polimorfica).** Una sola tabla
`translations(entity_type, entity_id, field, locale, value)`. Cada texto
bilingue (`role`, `summary`, `title`, `motivation`, ...) es N filas (una por
locale). `entity_type` es un ENUM, `field` un texto, `locale` un ENUM
`es|en`. PK compuesta `(entity_type, entity_id, field, locale)`. Escala a N
idiomas sin `ALTER TABLE`.

**c) Listas de texto plano** (`responsibilities`, `achievements` de
experience) — son listas ordenadas y bilingues. Se modelan como tabla
`experience_bullets(id, experience_id, kind, position)` + sus textos en
`translations`. `kind` ENUM `responsibility|achievement`.

**d) Vocabularios compartidos normalizados:**
- `niches` — catalogo de los 5 niches (seed fijo).
- `skills` — los strings sueltos de `skill_categories.skills[]` y de
  `experience.skillsTechnical/skillsSoft` se unifican en una tabla `skills`
  deduplicada (`name` UNIQUE).
- `tech_tags` — el `stack[]` de projects se normaliza a `tech_tags`
  (`name` UNIQUE). Se mantiene separado de `skills` porque su semantica es
  distinta (stack de un proyecto vs competencia declarada).

**e) Relaciones N:M** — tablas de union puras `(a_id, b_id)` con PK
compuesta: `experience_niches`, `project_niches`, `experience_skills`,
`skill_category_skills`, `project_tech_tags`, etc.

**f) Priority por (entidad, niche).** Tabla generica
`niche_priorities(entity_type, entity_id, niche_id, priority)` — separada de
las uniones de niche (decision del usuario: "union simple + priority
aparte"). PK `(entity_type, entity_id, niche_id)`.

**g) Estructuras embebidas de project** (`caseStudyDetailed`, `metrics`):
- `caseStudyDetailed` (problem/process/result, bilingue) — tabla 1:1
  `project_case_studies(project_id PK)` + sus textos en `translations`.
- `metrics` (`{market, product, architecture}` — claves variables) — tabla
  `project_metrics(id, project_id, metric_key, metric_value, position)`.

### Decisiones clave

- **Decision 1: tabla `translations` polimorfica unica** — el usuario
  eligio "tabla de traducciones separada". Una sola tabla generica (vs una
  `*_translations` por entidad) reduce la cantidad de tablas y unifica el
  patron. Trade-off: no hay FK real de `translations.entity_id` a cada tabla
  (es polimorfica); se cubre con un trigger de validacion + `entity_type`
  ENUM. Cardinalidad N idiomas sin migracion de schema.

- **Decision 2: 3NF completa con vocabularios deduplicados** — el usuario
  eligio "normalizacion completa". `skills` y `tech_tags` se deduplican: el
  string `"TypeScript"` que aparece en 8 YAML distintos es UNA fila. Permite
  queries tipo "todas las experiencias con skill X" y evita drift de
  nombres.

- **Decision 3: `skills` vs `tech_tags` separados** — aunque ambos son
  "etiquetas de texto", `skill_categories.skills[]` modela competencias
  agrupadas por dominio y `project.stack[]` modela el stack tecnico de un
  proyecto. Mezclarlos forzaria semantica ambigua. Dos vocabularios, cada uno
  con su tabla de union.

- **Decision 4: `niche_priorities` generica** — el priority depende del par
  (entidad, niche): `destacame-architect` tiene `priority 100` en fintech y
  `50` en generic. Una tabla generica polimorfica (igual patron que
  `translations`) lo modela en 3NF sin redundar la columna en cada union.
  Solo `experiences` y `projects` declaran priority hoy; la tabla lo soporta
  para cualquier entidad futura.

- **Decision 5: UUIDv7 como PK + `slug` UNIQUE** — PostgreSQL 18 trae
  `uuidv7()` nativo (ordenable temporalmente, mejor para indices que uuid v4).
  El `slug` se conserva como clave natural UNIQUE: es el identificador de los
  YAML actuales y lo que el seed usa para resolver FKs.

- **Decision 6: SQLAlchemy 2.x + Alembic, asumiendo el 2do sistema de
  migracion** — el usuario lo eligio explicitamente. Convive con el runner
  SQL del backend (`serverless/migrations/`). Para que NO se pisen: el CV usa
  Alembic con su propia tabla de version (`alembic_version`) y un
  `version_table_schema`/naming distinto; el runner SQL del backend sigue con
  su `schema_migrations`. Ambos sobre la misma DB, distinto registro de
  versiones. Los modelos SQLAlchemy declarativos son la fuente del
  autogenerate.

- **Decision 7: la DB es la fuente, el frontend la consume en build-time** —
  un script de build (`packages/content`) conecta a Neon, hace las queries,
  y emite la data que Astro consume. El sitio sigue 100% estatico en
  Cloudflare Pages. Esta tarea NO implementa ese script (ver seccion 8 y
  Fuera de alcance); entrega el schema + ER + seed.

### Ubicacion de los archivos

```text
db/cv/                              # nuevo arbol para el schema del CV
├── models/                         # modelos SQLAlchemy 2.x declarativos
│   ├── __init__.py                 # Base + re-exports
│   ├── base.py                     # DeclarativeBase + mixins (timestamps)
│   ├── enums.py                    # ENUMs Python <-> PG (locale, seniority...)
│   ├── catalog.py                  # niches, skills, tech_tags
│   ├── profile.py                  # profile + profile_stats
│   ├── experience.py               # experiences + experience_bullets
│   ├── project.py                  # projects + project_case_studies + project_metrics
│   ├── cv_entities.py              # certificates, awards, education, references, languages, skill_categories, publications
│   ├── junctions.py                # todas las tablas de union N:M
│   └── translations.py             # translations + niche_priorities
├── alembic/                        # migraciones Alembic del CV
│   ├── env.py                      # target_metadata = Base.metadata
│   ├── alembic.ini
│   └── versions/                   # NNN_*.py autogeneradas
├── seed/
│   └── seed_from_yaml.py           # carga la data real de los YAML a la DB
├── ddl/
│   └── schema.sql                  # DDL plano de referencia (CREATE TABLE ...)
└── README.md                       # como correr migraciones + seed
docs/diagrams/
└── cv-er.mmd                       # diagrama ER (Mermaid erDiagram)
```

> `db/cv/` es un arbol nuevo (no `serverless/`): el CV es un dominio
> distinto del backend serverless. Python 3.14 (alineado con `devtools/`).

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given los modelos SQLAlchemy del CV, When se corre
  `alembic upgrade head` contra una DB PostgreSQL 18 limpia, Then se crean
  todas las tablas del schema sin error.
- **AC-2**: Given el schema aplicado, When se inspecciona `translations`,
  Then ningun texto bilingue (`role`, `summary`, `title`, ...) vive como
  columna en la tabla de su entidad — todos estan en `translations` con su
  `locale`.
- **AC-3**: Given una experiencia con `priority {fintech:100, generic:50}`,
  When se consulta `niche_priorities`, Then hay 2 filas para esa experiencia
  con el priority correcto por niche, y la tabla de union `experience_niches`
  NO tiene columna `priority`.
- **AC-4**: Given el string `"TypeScript"` presente en multiples YAML, When
  se corre el seed, Then existe exactamente 1 fila en `skills` (o
  `tech_tags`) con ese nombre, referenciada por todas las uniones.
- **AC-5**: Given el seed ejecutado sobre el schema, When se cuentan las
  filas, Then `experiences=9`, `projects=6`, `certificates=11`, `awards=2`,
  `education=3`, `references=10`, `languages=2`, `skill_categories=10`,
  `profile=1`, y `translations` tiene 2 filas (es+en) por cada texto bilingue.
- **AC-6**: Given una entrada en `translations` con `entity_type='project'`
  y un `entity_id` inexistente en `projects`, When se intenta insertar, Then
  el trigger de integridad polimorfica la rechaza.
- **AC-7**: Given el seed ejecutado dos veces seguidas, When termina la 2da
  corrida, Then el resultado es identico al de la 1ra (idempotente, via
  `ON CONFLICT` por `slug`/clave natural).
- **AC-8**: Given el diagrama `cv-er.mmd`, When se renderiza, Then muestra
  las ~24 tablas con sus columnas, tipos, PK/FK y la cardinalidad de cada
  relacion.

## 4. Diagrama de Flujo (Antes y Despues)

### Antes

```text
packages/content/src/data/*.yaml  (fuente de verdad)
        |
        v  loadYamlEntries + Zod (build-time)
   frontend Astro  -->  sitio estatico
```

### Despues

```text
PostgreSQL (Neon, schema public)  (fuente de verdad)
        ^
        |  alembic upgrade head  (schema)
        |  seed_from_yaml.py     (data inicial, una vez)
        |
   modelos SQLAlchemy
        |
        v  script de build (FUERA DE ALCANCE de este plan)
   data exportada  -->  frontend Astro  -->  sitio estatico
```

## 5. Diagrama ER

Aplica: el nucleo de la tarea. ASCII resumido abajo; el `.mmd` completo
(seccion 7) lleva todas las columnas. `(*)` = tabla nueva (todas lo son).

```text
                          niches(*)                  translations(*)
                          - id uuid PK               - entity_type enum  PK
                          - slug string UNIQUE        - entity_id uuid    PK
                          - position int              - field string     PK
                               |                      - locale enum       PK
          +--------------------+---------+             - value text
          |                              |           (polimorfica: validada por trigger)
   experience_niches(*)            project_niches(*)
   - experience_id FK ─┐           - project_id FK ─┐  niche_priorities(*)
   - niche_id FK ──────┘           - niche_id FK ───┘  - entity_type enum PK
          |                              |             - entity_id uuid  PK
          |                              |             - niche_id FK     PK
   experiences(*)                  projects(*)         - priority int
   - id uuid PK                    - id uuid PK
   - slug UNIQUE                   - slug UNIQUE
   - company string                - name string
   - company_url string?           - status enum
   - start_ym string                - project_type enum
   - end_ym string?                  - is_confidential bool
   - seniority enum                  - url string? / repo string?
   - created_at/updated_at              |
        |                               +── project_case_studies(*) 1:1
        +── experience_bullets(*)        |    - project_id PK FK
        |    - id PK                      +── project_metrics(*) 1:N
        |    - experience_id FK           |    - id PK / project_id FK
        |    - kind enum                  |    - metric_key / position
        |    - position int               +── project_tech_tags(*) N:M
        +── experience_skills(*) N:M           - project_id FK / tech_tag_id FK
             - experience_id FK
             - skill_id FK            tech_tags(*)        skills(*)
                                      - id uuid PK        - id uuid PK
                                      - name UNIQUE       - name UNIQUE

   profile(*) 1 ── profile_stats(*) 1:1
   skill_categories(*) ──< skill_category_skills(*) >── skills(*)
   skill_categories(*) ──< skill_category_niches(*) >── niches(*)
   certificates / awards / education / references / languages / publications (*)
     cada una ──< <entidad>_niches(*) >── niches(*)
   (sus textos bilingues -> translations ; su priority -> niche_priorities)
```

Tipos PostgreSQL usados: `uuid` (PK, default `uuidv7()`), `text`/`varchar`,
`boolean`, `integer`, `timestamptz`, ENUMs nativos. Las fechas `YYYY-MM` del
CV se guardan como `varchar(7)` con `CHECK` regex (no son fechas completas;
fiel al dato actual). `certificates.date`/`awards.date` que son `YYYY-MM-DD`
o `YYYY-MM` se guardan como `date` (cert) y `varchar(7)` (award) segun su
formato real.

Relaciones (cardinalidad): `──<` 1:N, `>──<` N:M (via union), `──` 1:1.

## 6. Tests Requeridos

### 6.A. Migraciones (Alembic)

- `alembic upgrade head` sobre una DB limpia (branch Neon efimero) crea el
  schema sin error [AC-1]. `alembic downgrade base` lo revierte limpio.

### 6.B. Unit / integration tests (pytest, en `db/cv/tests/`)

- `test_schema_translations_no_inline_bilingual` — introspecta el schema,
  verifica que ninguna tabla de entidad tiene columnas `*_es`/`*_en` [AC-2].
- `test_niche_priority_separate` — `experience_niches` no tiene columna
  `priority`; `niche_priorities` tiene la fila esperada [AC-3].
- `test_seed_dedupes_vocabulary` — tras el seed, `skills` y `tech_tags` no
  tienen nombres duplicados [AC-4].
- `test_seed_row_counts` — conteos exactos por tabla tras el seed [AC-5].
- `test_translations_polymorphic_integrity` — insertar una traduccion con
  `entity_id` huerfano falla [AC-6].
- `test_seed_idempotent` — correr el seed 2 veces deja el mismo estado
  (mismos conteos, mismos ids por slug) [AC-7].
- Coverage pytest >= 80% en el codigo del seed y de los modelos con logica.
- Mockear: nada de DB — los tests corren contra un branch Neon efimero o un
  Postgres local en container (decidir en implementacion). NO mockear la DB
  (un test de schema mockeado no prueba el schema).

### 6.C. Typecheck / lint

- Ruff sobre `db/cv/` (Python 3.14, config alineada con `devtools/`).
- `mypy` o el type-check de Ruff sobre los modelos SQLAlchemy (SQLAlchemy
  2.x tiene typing nativo via `Mapped[...]`).

### 6.D. E2E Tests

N/A — no hay flujo de UI nuevo; la integracion con el frontend esta fuera
de alcance.

## 7. Archivos Afectados

### Crear

- `db/cv/models/base.py` — `DeclarativeBase`, mixin `TimestampMixin`
  (`created_at`/`updated_at timestamptz`)
  - Verificar: `python -c "from db.cv.models import Base"` sin error
- `db/cv/models/enums.py` — ENUMs: `locale_enum(es,en)`,
  `seniority_enum`, `project_type_enum`, `project_status_enum`,
  `skill_kind_enum`, `bullet_kind_enum`, `entity_type_enum`
- `db/cv/models/catalog.py` — `niches`, `skills`, `tech_tags`
- `db/cv/models/profile.py` — `profile`, `profile_stats`
- `db/cv/models/experience.py` — `experiences`, `experience_bullets`
- `db/cv/models/project.py` — `projects`, `project_case_studies`,
  `project_metrics`
- `db/cv/models/cv_entities.py` — `certificates`, `awards`, `education`,
  `references`, `languages`, `skill_categories`, `publications`
- `db/cv/models/junctions.py` — `experience_niches`, `project_niches`,
  `certificate_niches`, `award_niches`, `education_niches`,
  `reference_niches`, `language_niches`, `publication_niches`,
  `skill_category_niches`, `experience_skills`, `skill_category_skills`,
  `project_tech_tags`
- `db/cv/models/translations.py` — `translations`, `niche_priorities`
- `db/cv/models/__init__.py` — re-exporta `Base` + todos los modelos
- `db/cv/alembic/env.py` + `alembic.ini` — `target_metadata = Base.metadata`,
  `version_table='cv_alembic_version'` (no colisiona con el runner del
  backend)
  - Verificar: `alembic revision --autogenerate -m "init cv schema"` genera
    una migracion no vacia
  - Verificar: `alembic upgrade head` sobre branch Neon limpio sin error
- `db/cv/ddl/schema.sql` — DDL plano de referencia (export del schema, util
  para leerlo sin Python)
  - Verificar: `psql -f schema.sql` sobre DB limpia sin error
- `db/cv/seed/seed_from_yaml.py` — lee los YAML de
  `packages/content/src/data/`, resuelve vocabularios deduplicados, inserta
  con `ON CONFLICT` idempotente
  - Verificar: `python db/cv/seed/seed_from_yaml.py` + conteos [AC-5]
- `db/cv/tests/test_schema.py`, `test_seed.py` — los tests de seccion 6.B
  - Verificar: `pytest db/cv/tests/`
- `db/cv/pyproject.toml` + `uv.lock` — deps: `sqlalchemy>=2.0`, `alembic`,
  `psycopg[binary]`, `pyyaml`, `pytest`
- `db/cv/README.md` — comandos de migracion + seed + como conectar a Neon
- `docs/diagrams/cv-er.mmd` — `erDiagram` Mermaid con las ~24 tablas
  - Verificar: render del `.mmd` sin error de sintaxis

### Modificar

- `.claude/rules/neon-management.md` — agregar nota: el CV usa Alembic
  (`cv_alembic_version`), separado del runner SQL del backend
  - Verificar: lectura — coherencia con la decision 6
- `CLAUDE.md` (raiz) — agregar `db/cv/` al arbol del repo y a la tabla de
  navegacion
  - Verificar: lectura

### Fuera de alcance (tareas posteriores)

- El script de build que exporta la DB a la data que consume Astro
  (Decision 7). Esta tarea entrega schema + ER + seed; la inversion del
  flujo de build es una feature aparte.
- Eliminar los YAML actuales — se mantienen hasta que el build-from-DB
  exista y este verificado.

## 8. Descomposicion para Paralelizacion

Large (>20 archivos nuevos). Implementacion secuencial recomendada por
dependencias fuertes (los modelos preceden a Alembic, Alembic precede al
seed, el seed precede a los tests). NO se paraleliza con worktrees: las
tablas se referencian entre si (FKs) y `Base.metadata` es un punto unico.

Orden: enums + base -> catalog -> entidades -> junctions + translations ->
`__init__` -> Alembic env + autogenerate -> DDL export -> seed -> tests ->
diagrama -> docs.

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] AC-1..AC-8 numerados y referenciados por tests
- [ ] Branch Neon efimero disponible para correr migraciones de prueba
- [ ] `db/cv/pyproject.toml` con deps; `uv sync` sin warnings
- [ ] Confirmado que `cv_alembic_version` no colisiona con
      `schema_migrations` del runner del backend

### Definition of Done

- [ ] `alembic upgrade head` + `downgrade base` corren limpio en un branch
      Neon efimero [AC-1]
- [ ] Todos los AC tienen al menos un test que los cubre y pasa
- [ ] `pytest db/cv/tests/` verde; coverage >= 80% en seed y modelos con logica
- [ ] Ruff sin errores sobre `db/cv/`
- [ ] `db/cv/ddl/schema.sql` aplica sobre una DB limpia sin error
- [ ] El seed corre idempotente (2 corridas, mismo estado) [AC-7]
- [ ] `docs/diagrams/cv-er.mmd` renderiza sin error y refleja el schema final
- [ ] `db/cv/README.md` documenta los comandos de migracion + seed
- [ ] El branch Neon de prueba se elimina al cerrar
