# 05 — Fase 2: export DB→YAML, backup semanal y seed desde S3

> La DB es la fuente de verdad; el YAML pasa de "fuente" a "snapshot de
> backup". [Volver al README](README.md).

## 2.1 Script devtools `db_export`

Nuevo script `devtools/db_export/` (main.py + flags.py + README.md,
mono-comando con flags):

```bash
python devtools/run.py db_export --stage=dev --aws-profile=tfs-dev [--dry-run] [--out=tmp/db-export]
```

- Resuelve la Neon URL desde SSM (`/portfolio/{stage}/neon-url`) con
  boto3 — hermetico: NUNCA imprime el valor (mismo estandar que
  `secrets_sync`).
- Lee todas las entidades CV con queries SQLAlchemy (reusa
  `shared.db.cv_repository` / modelos concretos) y genera YAML
  **seed-compatible**: un archivo por entry con el mismo shape que
  consumia el seed (`slug`, BiLang, `niches`, `priority`, bullets,
  metrics, stack, ...), mas `profile.yaml`.
- Sube a S3: `s3://portfolio-db-backups/{stage}/{YYYY-MM-DD}/<entidad>/
  <slug>.yaml` y replica a `{stage}/latest/`. Con `--out` tambien deja
  copia local en `./tmp/` (debug).
- Round-trip garantizado por test: export → seed(restore) → export
  produce YAML identico (fixture en branch Neon de prueba o con session
  mockeada a nivel unit).

Tests: `devtools/tests/db_export/` (parsing de flags, serializacion YAML
por entidad con asserts exactos, layout S3). Ruff + coverage devtools.

## 2.2 Workflow `db-backup.yml`

`.github/workflows/db-backup.yml`:

- `on: schedule: cron '0 6 * * 1'` (lunes 06:00 UTC) + `workflow_dispatch`
  (input opcional `stage`).
- Job unico (matrix `stage: [dev, prod]`): checkout → setup Python/uv →
  OIDC `role-to-assume: portfolio-db-backup` →
  `python devtools/run.py db_export --stage=${{ matrix.stage }}`.
- `concurrency: db-backup` con `cancel-in-progress: false`.
- Sin secretos de GitHub: todo via OIDC + SSM.

## 2.3 Seed desde S3 + guard

`services/db` (command `seed`):

- `data.args.source`: prefijo S3 (`s3://portfolio-db-backups/dev/latest/`
  por default segun stage; o un path fechado para restore puntual). El
  loader baja los YAML del prefijo (boto3 S3 via `shared.aws.s3`) en vez
  de leer `core/seeds/data/` local.
- Guard nuevo: si las tablas CV tienen filas y NO viene
  `confirm_overwrite: true` → aborta con `4xxx SEED_REQUIRES_CONFIRM`
  (AC-9). El seed es ahora un mecanismo de RESTORE, no de sync rutinario.
- `manifest.yaml` de `db`: agregar `uses.buckets: db-backups (read)`.
- Events: actualizar `events/seed.json` + nuevo
  `events/restore.json` (`{command:'seed', args:{source, confirm_overwrite}}`).

## 2.4 Eliminar `seeds/data/` del repo

Orden NO negociable (gate antes del `git rm`):

1. Correr `db_export --stage=dev` y `--stage=prod` → snapshots `latest/`
   verificados en S3 (listado + spot-check de 2-3 YAML descargados).
2. Smoke de restore en un branch Neon efimero: seed desde
   `dev/latest/` con `confirm_overwrite` → `tables` muestra los counts
   esperados.
3. Recien entonces: `git rm -r serverless/lambda/services/db/core/seeds/data/`
   (conservar el codigo del seed/loader).
4. Actualizar referencias: `.claude/rules/neon-management.md` (seed →
   restore desde S3), `.claude/docs/serverless-backend/`, README del
   Lambda `db`, y la rule/skill que mencione `seeds/data`.

## Tests requeridos (seccion 6 de esta fase)

- 6.A TDD: `WHEN db_export THEN YAML seed-compatible por entidad [AC-8]`;
  `WHEN seed sin confirm sobre tablas pobladas THEN aborta [AC-9]`;
  `WHEN seed con source S3 THEN carga del prefijo [AC-9, AC-10]`.
- 6.B Unit: devtools (`test_runner --module=devtools --type=unit`) +
  Lambda db (`serverless tests --type=unit --lambda=db`).
- Workflow: validar sintaxis con `act -n` (skill github-actions) o
  `gh workflow view` tras push.

## Archivos afectados (Fase 2)

### Crear

- `devtools/db_export/{__init__,main,flags,exporter,s3_writer}.py` + README
  - Verificar: `python devtools/run.py test_runner --module=devtools --type=unit`
- `.github/workflows/db-backup.yml` — cron semanal + dispatch
  - Verificar: dispatch manual en dev → objetos en S3 (AC-8)
- `serverless/lambda/services/db/events/restore.json`
  - Verificar: `serverless run --stage=local --lambda=db --event=events/restore.json` (contra branch de prueba)

### Modificar

- `serverless/lambda/services/db/core/services/seed_service.py` — fuente
  S3 + guard `confirm_overwrite`
  - Verificar: `serverless tests --type=unit --lambda=db`
- `serverless/lambda/services/db/manifest.yaml` — `uses.buckets`
  - Verificar: `serverless deploy --lambda=db --stage=dev` + `status`
- `.claude/rules/neon-management.md` + docs del backend — seed→restore
  - Verificar: lectura cruzada sin referencias muertas a `seeds/data`

### Eliminar

- `serverless/lambda/services/db/core/seeds/data/**` — TRAS el gate 2.4
  - Verificar: `rg -l "seeds/data" serverless devtools .claude .github` → solo
    referencias historicas/changelog
