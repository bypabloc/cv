---
description: "Gestion operativa de Neon PostgreSQL en el backend serverless del portfolio: connection string en SSM, runner de migrations versionado, branches git-style, comandos devtools, reglas de seguridad y rollback"
globs: "serverless/migrations/**/*.sql,serverless/scripts/migrate.py,devtools/serverless/database.py"
---

# Gestion de Neon PostgreSQL - Portfolio

> Como se gestiona Neon en este proyecto. Neon es la unica DB SQL del
> portfolio: vive en `us-east-1`, almacena los datos analiticos del backend
> serverless (contacts + tracking events) que llegan via DynamoDB Streams.
>
> Esta rule cubre la **operacion** (connection string, migrations, branches,
> rollback, seguridad). Para arquitectura, pricing, comparativas y patrones
> de integracion Lambda, invocar la skill `neon` o leer `.claude/docs/neon/`.

## Activacion

Aplica SIEMPRE que se trabaje con:

- Archivos `.sql` bajo `serverless/migrations/`
- `serverless/scripts/migrate.py` (runner de migrations)
- `devtools/serverless/database.py` (comandos `serverless db-*`)
- Connection string de Neon en SSM (`/portfolio/neon-url`)
- Branches de Neon (testing, recovery, per-PR)
- Cualquier consulta SQL contra la DB del portfolio

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** leer la connection string desde SSM Parameter Store
  (`/portfolio/neon-url`, `/portfolio/dev/neon-url`, `/portfolio/prod/neon-url`),
  type `SecureString`. NUNCA hardcodear `DATABASE_URL` ni `DB_URL` en codigo,
  `template.yaml`, `samconfig.toml` ni archivos `.env` commiteados.
- **SIEMPRE** usar el endpoint **pooled** (`-pooler` en el host) para las
  Lambdas. El endpoint directo solo para `psql` interactivo o `migrate.py`.
- **SIEMPRE** agregar `sslmode=require&channel_binding=require` a la URL.
- **SIEMPRE** usar `psycopg` v3 — NUNCA `psycopg2` (deprecado).
- **SIEMPRE** versionar el schema en `serverless/migrations/` con archivos
  numerados `NNN_<nombre>.sql` + su par `NNN_<nombre>.down.sql`.
- **NUNCA** modificar el schema de Neon a mano via `psql` o la consola web —
  todo cambio de schema pasa por una migration nueva (auditabilidad).
- **NUNCA** editar una migration ya aplicada en `prod`. El runner valida
  `checksum` (SHA256) en `schema_migrations`; cambiar el SQL rompe la
  integridad. Crear una migration nueva.
- **NUNCA** correr `down`/`rollback` contra `prod` sin `--confirm` y sin
  haber probado el `.down.sql` antes en un branch Neon.
- **NUNCA** crear ni borrar el branch `main` de Neon — es la rama de
  produccion, inmutable.
- El auto-suspend tras 5 min de inactividad es **normal y sin costo** — no
  es un bug, no requiere accion.

## Entorno actual (mayo 2026)

| Aspecto | Valor |
|---------|-------|
| Provider | Neon serverless PostgreSQL |
| Region | `us-east-1` (misma que las Lambdas y SES) |
| Plan | Free tier (perpetuo: 100 CU-hours/mes, 0.5 GB/branch, 5 GB egress) |
| Version PG | 18 GA (asynchronous I/O) |
| Driver | `psycopg` v3 (TCP, endpoint pooled) |
| Connection string | SSM Parameter Store, `SecureString` |
| Branch produccion | `main` (inmutable) |

### Parametros SSM por stage

`devtools/serverless/database.py` resuelve el nombre asi:

| Stage | Parametro SSM |
|-------|---------------|
| `local` | `/portfolio/neon-url` |
| `dev` | `/portfolio/dev/neon-url` |
| `prod` | `/portfolio/prod/neon-url` |

Crear/rotar un parametro:

```bash
python devtools/run.py serverless setup-ssm --name=/portfolio/neon-url
```

## Migrations: el runner versionado

Las migrations viven en `serverless/migrations/` como pares de archivos:

```text
serverless/migrations/
├── 001_init_schema.sql           # forward
├── 001_init_schema.down.sql      # rollback
├── 002_indexes.sql
├── 002_indexes.down.sql
├── 005_migrations_log.sql        # crea la tabla schema_migrations
└── 005_migrations_log.down.sql
```

### Como funciona `serverless/scripts/migrate.py`

- Lee `DB_URL` de env (lo inyecta devtools desde
  `docker/env/server/.{stage}` — categoria `server`).
- Itera `migrations/*.sql` en orden numerico ascendente.
- Mantiene la tabla `schema_migrations` (`version`, `checksum`, `duration_ms`)
  para no re-aplicar. Una migration ya registrada se salta.
- Cada migration corre dentro de **una transaccion**: si falla, `rollback`
  completo (no deja el schema a medias).
- `down` revierte en orden inverso usando los `.down.sql`.

### Comandos del runner

```bash
cd serverless

# Aplicar todas las pendientes (default)
DB_URL=<...> python scripts/migrate.py up

# Ver estado: applied / pending
DB_URL=<...> python scripts/migrate.py status

# Rollback (todas, o hasta una version con --target)
DB_URL=<...> python scripts/migrate.py down --target=003
```

### Comandos via devtools CLI (forma preferida)

`devtools/serverless/database.py` resuelve la URL desde SSM automaticamente —
no hay que exportar `DB_URL` a mano:

```bash
python devtools/run.py serverless db-migrate --stage=dev          # aplicar pendientes
python devtools/run.py serverless db-migrate --stage=dev --dry-run # ver que correria
python devtools/run.py serverless db-rollback --stage=dev --confirm # rollback ultima
python devtools/run.py serverless db-tables --stage=dev           # tablas + row counts
python devtools/run.py serverless db-shell --stage=dev            # psql interactivo
python devtools/run.py serverless db-seed --stage=local           # data de prueba
```

`db-rollback` exige `--confirm` (es destructivo). Requiere `psql` instalado
(`apt install postgresql-client`).

## Crear una migration nueva

1. Elegir el siguiente numero correlativo (`006_...`).
2. Crear el par de archivos:

```bash
cat > serverless/migrations/006_<nombre>.sql <<'EOF'
-- forward: descripcion de que hace
ALTER TABLE contacts ADD COLUMN last_contact_at timestamptz;
EOF

cat > serverless/migrations/006_<nombre>.down.sql <<'EOF'
-- rollback exacto del forward
ALTER TABLE contacts DROP COLUMN last_contact_at;
EOF
```

3. **Probar en un branch Neon antes de tocar `dev`/`prod`** (ver abajo).
4. Aplicar: `python devtools/run.py serverless db-migrate --stage=dev`.
5. Verificar: `python devtools/run.py serverless db-tables --stage=dev`.

Reglas para el SQL de la migration:

- El `.down.sql` debe revertir EXACTAMENTE el `.sql` (idempotente al volver).
- Sin `BEGIN`/`COMMIT` dentro del archivo — el runner ya envuelve en
  transaccion. (Excepcion: `CREATE INDEX CONCURRENTLY`, que no puede ir en
  transaccion — si se usa, documentarlo y aplicarlo aparte.)
- Cambios destructivos (`DROP COLUMN`, `DROP TABLE`) requieren migration
  separada y revision explicita.
- Una migration = un cambio logico coherente.

## Branches Neon: testing, recovery, per-PR

Un branch de Neon es un clon instantaneo (copy-on-write, ~1 seg, sin costo de
storage hasta que diverge). Usos en este proyecto:

```bash
# Listar branches
python devtools/run.py serverless db-branch list

# Crear branch para probar una migration nueva (antes de tocar prod)
python devtools/run.py serverless db-branch create --branch=test-006-migration --parent=main

# Borrar el branch cuando termina la prueba (exige --confirm)
python devtools/run.py serverless db-branch delete --branch=test-006-migration --confirm
```

Tambien via `neon` CLI directo (`npm i -g neonctl`):

```bash
neon branches list
neon branches create --name test-X --parent main
neon branches delete test-X
```

Workflow obligatorio para una migration de schema:

```text
1. crear branch:  db-branch create --branch=test-NNN --parent=main
2. apuntar DB_URL al branch y correr migrate up + down (probar ambos)
3. validar queries que usan el cambio
4. si OK  -> aplicar la migration a dev, luego prod
5. si mal -> iterar; el branch se descarta sin afectar main
6. borrar branch:  db-branch delete --branch=test-NNN --confirm
```

Recovery point-in-time: crear un branch desde un `--lsn` o timestamp pasado
(retencion 7 dias en Free tier). No reemplaza tener `.down.sql` correctos.

## Conexion desde las Lambdas

Patron obligatorio (detalle completo en
`.claude/docs/neon/02-aws-lambda-integration-python.md`):

- Connection string **pooled** leida de SSM en el **cold start** del Lambda
  (module scope), NO dentro del handler — se reutiliza entre invocaciones del
  mismo contenedor.
- `psycopg` v3, `sslmode=require&channel_binding=require`.
- El Lambda que escribe a Neon es el `stream_processor` (consume DynamoDB
  Streams). El form de contacto y el tracking pixel escriben primero a
  DynamoDB; Neon es la capa analitica downstream.

## Seguridad

- La connection string es un secreto: SSM `SecureString`, IAM scoped al
  parametro especifico (`ssm:GetParameter` sobre el ARN exacto, no `ssm:*`).
- NUNCA logear la `DATABASE_URL` ni la password. En logs, referirse al host
  o al stage, nunca a la URL completa.
- NUNCA commitear la URL. `DB_URL` es categoria `server`: vive en
  `docker/env/server/.{stage}` (gitignored) como placeholder, o resuelta en
  runtime desde SSM. Solo el `docker/env/server/.example` se versiona, sin
  valores reales.
- Rotacion: regenerar la password en la consola Neon, actualizar el parametro
  SSM. Las Lambdas la releen en el siguiente cold start.

## Verificacion (antes de declarar listo)

Tras crear/modificar una migration:

```bash
# 1. Probar forward + rollback en un branch Neon
python devtools/run.py serverless db-branch create --branch=test-verify --parent=main
#    (apuntar al branch) migrate up && migrate down && migrate up

# 2. Estado de migrations coherente
python devtools/run.py serverless db-migrate --stage=dev --dry-run

# 3. Aplicar y verificar inventario
python devtools/run.py serverless db-migrate --stage=dev
python devtools/run.py serverless db-tables --stage=dev

# 4. Limpiar
python devtools/run.py serverless db-branch delete --branch=test-verify --confirm
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Modificar schema via `psql`/consola web | Sin auditabilidad, drift con `migrations/` | Migration numerada nueva |
| Editar un `.sql` ya aplicado en prod | Rompe el checksum de `schema_migrations` | Crear migration nueva |
| Hardcodear `DATABASE_URL` en codigo o `template.yaml` | Secreto expuesto en git | SSM Parameter Store |
| Endpoint directo (no `-pooler`) en Lambda | Agota `max_connections` bajo concurrencia | Endpoint pooled |
| `psycopg2` | Deprecado | `psycopg` v3 |
| Crear cliente DB dentro del handler | Cold start ~250ms cada invocacion | Module scope |
| `rollback` en prod sin probar el `.down.sql` | Puede dejar el schema inconsistente | Probar en branch Neon primero |
| Crear/borrar el branch `main` | Es la produccion | Branches efimeros desde `main` |
| Preocuparse por el auto-suspend de 5 min | Es normal y gratis | Ignorar; el resume es transparente |

## Schema del CV — Alembic (segundo sistema de migraciones)

El Neon del portfolio aloja DOS schemas con DOS sistemas de migracion
distintos sobre el MISMO schema `public`:

| Dominio | Tablas | Sistema | Tabla de versiones |
|---------|--------|---------|--------------------|
| Backend serverless | `contacts`, `tracking_events`, ... | runner SQL versionado (`serverless/scripts/migrate.py`) | `schema_migrations` |
| CV | `experiences`, `projects`, `translations`, ... | SQLAlchemy + Alembic (`db/cv/`) | `cv_alembic_version` |

Reglas duras para que NO se pisen:

- El CV usa Alembic con `version_table='cv_alembic_version'` — NUNCA
  `alembic_version` ni `schema_migrations`.
- El `env.py` del CV filtra el autogenerate con `include_name` /
  `include_object`: Alembic SOLO ve las tablas de `models.Base.metadata`.
  Sin ese filtro, `alembic revision --autogenerate` genera
  `DROP TABLE contacts` (destructivo) porque las tablas del backend no
  estan en su metadata.
- El runner SQL del backend NO debe tocar tablas del CV y viceversa.
- La connection string del CV es la misma `CV_DATABASE_URL` resuelta desde
  SSM (mismo patron de secretos que el resto).

Detalle operativo: `db/cv/README.md`.

## Referencias cruzadas

- Arquitectura, pricing, comparativas, integracion Lambda detallada:
  skill `neon` + `.claude/docs/neon/` (5 archivos)
- Backend serverless (estructura, diagramas, propuesta hibrida):
  `serverless/ARCHITECTURE.md` + `serverless/INTEGRATION.md`
- Schema de las tablas + queries analiticas:
  `.claude/docs/postgresql-18-analytics/README.md`
- Schema relacional del CV (SQLAlchemy + Alembic + seed): `db/cv/README.md`
- Secretos en SSM (patron general): `serverless/docs/secrets.md`
- PostgreSQL 18 (features del motor): skill `postgresql-18`
