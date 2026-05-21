---
description: "Gestion operativa de Neon PostgreSQL en el backend serverless del portfolio: connection string en SSM, migraciones Alembic via la Lambda db, branches git-style, comandos devtools, reglas de seguridad y rollback"
globs: "serverless/shared/db/**/*.py,serverless/src/db/**/*.py,devtools/serverless/database.py"
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

- Los modelos SQLAlchemy en `serverless/shared/db/`
- Las migraciones Alembic en `serverless/shared/db/alembic/`
- La Lambda `db` (`serverless/src/db/`)
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
  Lambdas. El endpoint directo solo para `psql` interactivo.
- **SIEMPRE** agregar `sslmode=require&channel_binding=require` a la URL.
- **SIEMPRE** usar `psycopg` v3 — NUNCA `psycopg2` (deprecado).
- **SIEMPRE** versionar el schema con los modelos SQLAlchemy de
  `serverless/shared/db/models/` + migraciones Alembic en
  `shared/db/alembic/versions/`. Es la unica fuente de verdad.
- **NUNCA** modificar el schema de Neon a mano via `psql` o la consola web —
  todo cambio de schema pasa por una migracion Alembic nueva (auditabilidad).
- **NUNCA** editar una migracion Alembic ya aplicada en `prod` — rompe la
  cadena de revisiones. Crear una migracion nueva.
- **NUNCA** correr `downgrade`/`rollback` contra `prod` sin `confirm` y sin
  haber probado el `downgrade()` antes en un branch Neon.
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

## Migrations: Alembic via la Lambda `db`

El schema lo definen los modelos SQLAlchemy de
`serverless/shared/db/models/` — esa es la unica fuente de verdad.
Las migraciones son archivos Alembic en
`serverless/shared/db/alembic/versions/`. La Lambda `db`
(`serverless/src/db/`) corre Alembic dentro de AWS; devtools la invoca.

> El runner SQL viejo (`migrate.py` + los `.sql` numerados +
> `schema_migrations`) esta archivado en `serverless/migrations/_archive/`
> — referencia historica, NO se aplica mas. Ver su README.

### Comandos via devtools CLI

`devtools/serverless/database.py` resuelve el stage e invoca la Lambda `db`
con `aws lambda invoke` — no hay que exportar `DB_URL` a mano:

```bash
python devtools/run.py serverless db-migrate --stage=dev            # alembic upgrade head
python devtools/run.py serverless db-migrate --stage=dev --dry-run  # ver que correria
python devtools/run.py serverless db-migrate --stage=dev --target=<rev>  # hasta una rev
python devtools/run.py serverless db-rollback --stage=dev --confirm # alembic downgrade -1
python devtools/run.py serverless db-current --stage=dev            # revision aplicada
python devtools/run.py serverless db-show-migrations --stage=dev    # historial
python devtools/run.py serverless db-tables --stage=dev             # tablas + row counts
python devtools/run.py serverless db-shell --stage=dev              # psql interactivo
```

`db-rollback` exige `--confirm` (es destructivo). `db-shell`/`db-tables`
requieren `psql` instalado (`apt install postgresql-client`); el resto no.

### Invocacion directa de la Lambda `db`

La Lambda `db` tiene estructura factory — el payload trae `command`:

```jsonc
{"command": "migrate"}                                  // upgrade head
{"command": "migrate", "args": {"target": "<rev>"}}
{"command": "current"}                                  // revision aplicada
{"command": "show-migrations"}                          // historial
{"command": "stamp", "args": {"target": "head"}}        // adoptar sin recrear
{"command": "downgrade", "args": {"target": "-1", "confirm": true}}
```

## Crear una migration nueva

1. Modificar los modelos SQLAlchemy en
   `serverless/shared/db/models/` (agregar columna, tabla, indice).
2. Autogenerar la migracion con Alembic (en local, con `DATABASE_URL`
   apuntando a un branch Neon de prueba):

   ```bash
   cd serverless
   DATABASE_URL=<branch-de-prueba> \
     .venv/bin/alembic -c shared/db/alembic.ini revision \
     --autogenerate -m "<descripcion>"
   ```

3. **Revisar el archivo generado** en `shared/db/alembic/versions/` —
   Alembic no autogenera todo (particiones, triggers, extensiones,
   `op.execute()` queda manual; ver `_init_schema_extras.py`).
4. **Probar `upgrade` + `downgrade` en un branch Neon** antes de tocar
   `dev`/`prod` (ver "Branches Neon" abajo).
5. Aplicar a dev: `python devtools/run.py serverless db-migrate --stage=dev`.
6. Verificar: `python devtools/run.py serverless db-current --stage=dev`.

Reglas para una migracion:

- El `downgrade()` debe revertir EXACTAMENTE el `upgrade()`.
- Cambios destructivos (`DROP COLUMN`, `DROP TABLE`) requieren migracion
  separada y revision explicita.
- Una migracion = un cambio logico coherente.
- NUNCA editar una migracion ya aplicada en prod (rompe la cadena de
  revisiones de Alembic). Crear una nueva.

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
(retencion 7 dias en Free tier). No reemplaza tener un `downgrade()`
correcto en cada migracion.

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

Tras crear/modificar una migracion Alembic:

```bash
# 1. Probar upgrade + downgrade + upgrade en un branch Neon de prueba
python devtools/run.py serverless db-branch create --branch=test-verify --parent=main
#    apuntar DATABASE_URL al branch y correr (en local, con el alembic del repo):
#      alembic -c shared/db/alembic.ini upgrade head
#      alembic -c shared/db/alembic.ini downgrade base
#      alembic -c shared/db/alembic.ini upgrade head

# 2. Ver que aplicaria sin ejecutar
python devtools/run.py serverless db-migrate --stage=dev --dry-run

# 3. Aplicar a dev y verificar
python devtools/run.py serverless db-migrate --stage=dev
python devtools/run.py serverless db-current --stage=dev
python devtools/run.py serverless db-tables --stage=dev

# 4. Limpiar el branch de prueba
python devtools/run.py serverless db-branch delete --branch=test-verify --confirm
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Modificar schema via `psql`/consola web | Sin auditabilidad, drift con los modelos | Migracion Alembic nueva |
| Editar una migracion Alembic ya aplicada en prod | Rompe la cadena de revisiones | Crear una migracion nueva |
| Hardcodear `DATABASE_URL` en codigo o `template.yaml` | Secreto expuesto en git | SSM Parameter Store |
| Endpoint directo (no `-pooler`) en Lambda | Agota `max_connections` bajo concurrencia | Endpoint pooled |
| `psycopg2` | Deprecado | `psycopg` v3 |
| Crear el engine SQLAlchemy dentro del handler | Cold start cada invocacion | Module scope (`get_engine` con lru_cache) |
| `downgrade` en prod sin probar el `downgrade()` | Puede dejar el schema inconsistente | Probar en branch Neon primero |
| Crear/borrar el branch `main` | Es la produccion | Branches efimeros desde `main` |
| Preocuparse por el auto-suspend de 5 min | Es normal y gratis | Ignorar; el resume es transparente |

## Schema unificado — un solo Alembic, una Lambda `db`

Desde mayo de 2026 el Neon del portfolio tiene UN solo schema gestionado
por UN solo Alembic. Antes habia dos sistemas (runner SQL para el backend
+ Alembic aparte para el CV); se unificaron.

| Aspecto | Valor actual |
|---------|--------------|
| Modelos (fuente de verdad) | `serverless/shared/db/models/` — 35 tablas SQLAlchemy 2.x (CV + datos del visitante) |
| Migraciones | un solo Alembic en `serverless/shared/db/alembic/` |
| Tabla de versiones | la estandar `alembic_version` |
| Runner | la Lambda `db` (`serverless/src/db/`) corre Alembic dentro de AWS |
| Comandos | `db-migrate`, `db-rollback`, `db-current`, `db-show-migrations` via `python devtools/run.py serverless <cmd>` |

Reglas duras:

- TODO cambio de schema (backend o CV) es una migracion Alembic nueva en
  `shared/db/alembic/versions/`. NO se editan los `.sql` archivados.
- El runner SQL viejo (`serverless/scripts/migrate.py` + los `.sql`) esta
  archivado en `serverless/migrations/_archive/` — solo referencia
  historica, NO se aplica mas.
- En prod (que ya tiene el schema creado por los `.sql` viejos) se corre
  `db-current` y, si hace falta adoptar Alembic, `{"command": "stamp"}` —
  NUNCA un `migrate` que intente recrear tablas existentes.
- La connection string es la `DATABASE_URL` que el template SAM inyecta
  desde SSM (`SSM_NEON_URL_PATH`); el modulo `shared/db/url.py` la
  resuelve. Mismo patron de secretos que el resto.

Detalle operativo: `serverless/shared/db/` (modelos + Alembic) y
`serverless/src/db/` (la Lambda).

## Referencias cruzadas

- Arquitectura, pricing, comparativas, integracion Lambda detallada:
  skill `neon` + `.claude/docs/neon/` (5 archivos)
- Backend serverless (estructura, diagramas, propuesta hibrida):
  `serverless/ARCHITECTURE.md` + `serverless/INTEGRATION.md`
- Schema de las tablas + queries analiticas:
  `.claude/docs/postgresql-18-analytics/README.md`
- Schema PostgreSQL unificado (modelos SQLAlchemy + Alembic):
  `serverless/shared/db/` + diagrama `docs/diagrams/db-er.mmd`
- Secretos en SSM (patron general): `serverless/docs/secrets.md`
- PostgreSQL 18 (features del motor): skill `postgresql-18`
