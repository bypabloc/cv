# SPEC-008: Neon project + migrations SQL 001-005 + psycopg3 layer

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: Neon dashboard, `serverless/migrations/`,
`serverless/src/layers/postgres_python/`, `serverless/template.yaml`
**Dependencias**: SPEC-001
**Paralelizable con**: SPEC-002 (no comparten archivos)

## 1. Contexto

Setup completo de la base analitica (Neon PostgreSQL 18) + schema
inicial + Lambda Layer con psycopg3 binary compiled para arm64.
Pre-requisito de SPEC-009 (stream_processor) y SPEC-010 (aggregator).

### Hallazgos de exploracion

- Skill `/neon` consolida setup en 5 docs
- Schema documentado en
  `.claude/docs/postgresql-18-analytics/02-schema-design-this-project.md`
- 5 migrations definidas en `serverless/ARCHITECTURE.md` seccion 1
- Free tier Neon: 0.5GB + 191.9h compute/mes + 10 branches (suficiente)

## 2. Solucion propuesta

### Setup Neon (manual)

1. Crear cuenta Neon (si no existe) en https://console.neon.tech
2. Crear project `portfolio-backend` region `us-west-2`
3. Habilitar extensions: `pg_partman` (para partitioning tracking_events)
4. Crear branch `main` (default) + `dev` para staging
5. Copiar connection string -> `serverless setup-ssm --name=/portfolio/neon-url`

### Migrations SQL

Crear `serverless/migrations/` con 5 archivos numerados:

```text
migrations/
├── 001_init_schema.sql              # contacts + tracking_events parent + processed_stream_events
├── 001_init_schema.down.sql         # DROP TABLE (rollback)
├── 002_indexes.sql                  # GIN to_tsvector + BRIN created_at + B-tree compuestos
├── 002_indexes.down.sql
├── 003_materialized_views.sql       # mv_contacts_by_month_niche + mv_session_journey + mv_top_landing_pages
├── 003_materialized_views.down.sql
├── 004_aggregates_tables.sql        # tracking_daily_aggregates + daily_metrics
├── 004_aggregates_tables.down.sql
├── 005_pg_partman_setup.sql         # config pg_partman para auto-create monthly partitions
└── 005_pg_partman_setup.down.sql
```

### Layer Python

Layer `postgres_python` con `psycopg[binary]>=3.2` compilado para arm64.
Separate de `common_python` para no inflar las Lambdas que no necesitan
PG (contact_form, tracking_pixel, turnstile_validator).

### Decisiones clave

- **Decision 1: Migrations versionadas con down scripts** — ya decidido
  en CLI `db-migrate`/`db-rollback`. Cada `.sql` tiene su `.down.sql`.
- **Decision 2: Schema_migrations table** — tabla simple
  `(version VARCHAR PRIMARY KEY, applied_at TIMESTAMPTZ)` para tracking.
  Migration runner (en `devtools/serverless/database.py`) verifica antes
  de aplicar.
- **Decision 3: Branch Neon `dev` desde main** — permite testing de
  migrations sin afectar main. Eliminable por la CLI `db-branch delete`.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given Neon project creado, When ejecuto `psql <connection>`,
  Then conexion exitosa
- **AC-2**: Given migration 001 aplicada, When ejecuto `\d contacts`
  en psql, Then tabla existe con CITEXT email, TEXT NOT NULL en
  campos required, JSONB metadata, UUIDv7 id
- **AC-3**: Given migration 002 aplicada, When ejecuto `SELECT
  indexname FROM pg_indexes WHERE tablename='contacts'`, Then incluye
  GIN sobre message + email + metadata
- **AC-4**: Given migration 003 aplicada, When ejecuto `\dm`, Then
  3 materialized views listadas
- **AC-5**: Given migration 005 aplicada + ejecuto
  `SELECT partman.run_maintenance()`, When inspecciono partitions de
  `tracking_events`, Then existen 2-3 partitions futuras (mes actual + 2)
- **AC-6**: Given Layer postgres_python en SAM, When inspecciono
  `.aws-sam/build/PostgresLayer/`, Then incluye `psycopg-3.2.*` con
  binarios arm64 compatibles
- **AC-7**: Given Lambda dummy importa psycopg3 desde Layer, When invoco
  Lambda, Then no falla con ImportError

## 4. Diagrama de Flujo

N/A — setup statico.

## 5. Diagrama ER

Documentado en `serverless/ARCHITECTURE.md` seccion 6.5. Verificar
sincronizacion entre el doc y los SQL escritos.

## 6. Tests Requeridos

### 6.B. Unit Tests

- `tests/unit/migrations/test_001_init_schema.py` — usa testcontainers
  con PostgreSQL 18 local, aplica migration, valida shape
- `tests/unit/migrations/test_002_indexes.py` — verifica indexes
  esperados
- `tests/unit/migrations/test_003_materialized_views.py` — verifica MV
  refresh manual
- `tests/unit/migrations/test_004_aggregates_tables.py`
- `tests/unit/migrations/test_005_pg_partman.py` — solo si pg_partman
  disponible en el container

Coverage de migrations es opcional. Lo critico es smoke test contra el
Neon dev branch.

### 6.E. Manual verification

```bash
# Aplicar migrations
python devtools/run.py serverless db-migrate --stage=dev --dry-run
python devtools/run.py serverless db-migrate --stage=dev

# Verificar tablas
python devtools/run.py serverless db-tables --stage=dev

# Verificar indexes
python devtools/run.py serverless db-shell --stage=dev
# > \d contacts
# > \di
# > \dm
```

## 7. Archivos Afectados

### Crear

- `serverless/migrations/001_init_schema.sql` — tablas: contacts,
  tracking_events (parent), processed_stream_events + schema_migrations
- `serverless/migrations/001_init_schema.down.sql`
- `serverless/migrations/002_indexes.sql` — GIN + BRIN + compuestos
- `serverless/migrations/002_indexes.down.sql`
- `serverless/migrations/003_materialized_views.sql`
- `serverless/migrations/003_materialized_views.down.sql`
- `serverless/migrations/004_aggregates_tables.sql` — tracking_daily_aggregates + daily_metrics
- `serverless/migrations/004_aggregates_tables.down.sql`
- `serverless/migrations/005_pg_partman_setup.sql` — config partition mensual
- `serverless/migrations/005_pg_partman_setup.down.sql`
- `serverless/src/layers/postgres_python/requirements.txt` —
  `psycopg[binary]>=3.2`
- `serverless/src/layers/postgres_python/README.md` — como compilar arm64
- `serverless/scripts/seed_test_data.sql` — sample data para
  `serverless db-seed`

### Modificar

- `serverless/template.yaml` — agregar `PostgresLayer` LayerVersion
- `serverless/docs/secrets.md` — documentar
  `/portfolio/neon-url` (rotation policy: manual cada 90 dias)

### Tareas post-deploy

- `serverless db-branch list` (verificar main + dev)
- `serverless db-migrate --stage=dev --dry-run`
- `serverless db-migrate --stage=dev`
- `serverless db-tables --stage=dev` (verificar AC-2)

## 8. Descomposicion para Paralelizacion

| Task | Archivos | Depende de | Paralelizable con |
|------|----------|------------|-------------------|
| T1 | 001_init_schema.sql + down | — | T2 (Layer) |
| T2 | Layer postgres_python + template.yaml | — | T1, T3 |
| T3 | 002_indexes.sql + down | T1 | — |
| T4 | 003_materialized_views.sql + down | T1 | T5 |
| T5 | 004_aggregates_tables.sql + down | T1 | T4 |
| T6 | 005_pg_partman_setup.sql + down | T1 | — |
| T7 | Tests migrations + deploy + verify | T1-T6 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-001 done (template SAM base)
- [ ] Cuenta Neon creada (manual)
- [ ] Connection string en SSM `/portfolio/neon-url`

### Definition of Done

- [ ] AC-1 a AC-7 cumplidos
- [ ] Las 5 migrations aplicables sin errores en branch `dev`
- [ ] Las 5 down migrations reversibles sin errores
- [ ] `serverless db-tables --stage=dev` lista las 6 tablas + 3 MVs
- [ ] `pg_partman.run_maintenance()` crea partitions automaticamente
- [ ] Tests de integracion testcontainers pasan localmente
- [ ] `serverless db-shell --stage=dev` permite query interactivo
