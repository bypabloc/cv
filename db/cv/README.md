# db/cv — Schema relacional del CV (PostgreSQL)

> Modela en PostgreSQL 18 la data del CV de Pablo Contreras que hoy vive como
> YAML en `packages/content/src/data/`. Schema normalizado a 3NF, migraciones
> con SQLAlchemy 2.x + Alembic, seed idempotente desde los YAML.

## Que hay aca

| Ruta | Que es |
|------|--------|
| `models/` | Modelos SQLAlchemy 2.x declarativos — fuente del autogenerate |
| `alembic/` | Migraciones versionadas (`alembic/versions/`) |
| `seed/seed_from_yaml.py` | Carga la data real de los YAML a la DB (idempotente) |
| `ddl/schema.sql` | DDL plano de referencia (generado, NO editar a mano) |
| `ddl/generate_schema_sql.py` | Regenera `schema.sql` desde los modelos |
| `tests/` | Tests pytest del schema + seed |
| `pyproject.toml` | Deps (`uv`): SQLAlchemy, Alembic, psycopg v3, pyyaml |

El diagrama ER esta en [`docs/diagrams/cv-er.mmd`](../../docs/diagrams/cv-er.mmd).

## Modelo de datos (resumen)

- **9 entidades** del CV: `profile` (+`profile_stats`), `experiences`
  (+`experience_bullets`), `projects` (+`project_case_studies`,
  `project_metrics`), `skill_categories`, `certificates`, `awards`,
  `education`, `references`, `languages`, `publications`.
- **3 vocabularios deduplicados**: `niches` (5 fijos), `skills`, `tech_tags`.
- **`translations`** — tabla polimorfica unica: todos los textos bilingues
  (`role`, `summary`, `title`, ...) como 1 fila por (entidad, campo, idioma).
- **`niche_priorities`** — tabla polimorfica con el `priority` por
  (entidad, niche).
- **12 tablas de union N:M** — `<entidad>_niches`, `experience_skills`,
  `skill_category_skills`, `project_tech_tags`.
- **Trigger `assert_entity_exists`** — valida la integridad del `entity_id`
  polimorfico de `translations` / `niche_priorities` (no puede ser FK real).

## Requisitos

- Python 3.14 + `uv` (la primera vez: `uv sync` en `db/cv/`).
- Una DB PostgreSQL 18. En este proyecto: el Neon del portfolio
  (`late-paper-11192344`). Para pruebas, crear un branch Neon efimero.

## Connection string — `CV_DATABASE_URL`

Ni Alembic ni el seed hardcodean la URL: la leen de la env var
`CV_DATABASE_URL`. NUNCA commitearla. En el flujo real se resuelve desde
SSM y se exporta puntualmente al comando (ver
[`.claude/rules/env-files.md`](../../.claude/rules/env-files.md)):

```bash
export CV_DATABASE_URL="postgresql://USER:PASS@HOST/neondb?sslmode=require"
```

Acepta `postgresql://` y `postgresql+psycopg://` (Alembic prefiere el
segundo; el seed normaliza al primero).

## Migraciones (Alembic)

```bash
cd db/cv

# Aplicar todas las migraciones pendientes
CV_DATABASE_URL="..." .venv/bin/alembic upgrade head

# Revertir la ultima / todas
CV_DATABASE_URL="..." .venv/bin/alembic downgrade -1
CV_DATABASE_URL="..." .venv/bin/alembic downgrade base

# Estado actual
CV_DATABASE_URL="..." .venv/bin/alembic current

# Autogenerar una migracion tras cambiar un modelo
CV_DATABASE_URL="..." .venv/bin/alembic revision --autogenerate -m "desc"
```

> **Importante**: revisar SIEMPRE la migracion autogenerada antes de
> aplicarla. Alembic detecta la mayoria de los cambios pero no todo
> (renombrar columna = drop + add, triggers custom, etc.).

### Aislamiento del backend serverless

El CV comparte el schema `public` del Neon con el backend serverless
(`contacts`, `tracking_events`, ...). Dos salvaguardas en `alembic/env.py`:

1. `version_table='cv_alembic_version'` — registro de versiones propio, NO
   colisiona con el `schema_migrations` del runner SQL del backend.
2. `include_name` / `include_object` — el autogenerate SOLO ve las tablas
   del CV. Sin este filtro, Alembic generaria `DROP TABLE contacts` y
   similares (porque esas tablas no estan en `Base.metadata`).

Si se agrega una tabla nueva al CV, queda cubierta automaticamente (el
filtro se deriva de `Base.metadata`).

## Seed

Carga la data real de los YAML del CV. Idempotente: correrlo N veces deja
el mismo estado (`ON CONFLICT` sobre la clave natural de cada tabla).

```bash
cd db/cv
# Pre-condicion: el schema ya aplicado (alembic upgrade head)
CV_DATABASE_URL="..." .venv/bin/python seed/seed_from_yaml.py
```

Imprime los conteos por tabla al terminar.

## DDL plano de referencia

`ddl/schema.sql` es material de lectura — la fuente de verdad del schema
son las migraciones. Regenerarlo tras cambiar los modelos:

```bash
cd db/cv
.venv/bin/python ddl/generate_schema_sql.py
```

## Tests

Corren contra una DB real (un branch Neon efimero), con el schema aplicado
y el seed ejecutado. Sin `CV_DATABASE_URL` se omiten (skip).

```bash
cd db/cv
CV_DATABASE_URL="..." .venv/bin/pytest tests/ -q
```

## Flujo recomendado para un cambio de schema

```text
1. Editar el/los modelo(s) en models/
2. alembic revision --autogenerate -m "desc"   (contra un branch Neon)
3. REVISAR la migracion generada en alembic/versions/
4. alembic upgrade head                         (branch de prueba)
5. python ddl/generate_schema_sql.py            (refrescar el DDL)
6. pytest tests/                                (verificar)
7. Aplicar a dev, luego prod
```

## Fuera de alcance (pendiente)

- El script de build que invierte el flujo: leer la DB y exportar la data
  que consume el frontend Astro (hoy lee los YAML directo). Hasta que ese
  script exista, los YAML siguen siendo la fuente que renderiza el sitio.
- Eliminar los YAML — se conservan hasta que el build-from-DB este listo.
