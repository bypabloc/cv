# 12 — Verificacion E2E iterativa (fase final)

[README](README.md) | [11-paralelizacion](11-paralelizacion-worktrees.md) |
**12-verificacion-e2e** | [13-mapeo](13-mapeo-usos-modelos.md)

## Regla de cierre (gate del PR)

`git push` + `gh pr create` SOLO ocurren cuando **toda** la bateria de
esta seccion pasa en verde. Hasta ese momento se itera:

```text
ejecutar bateria -> si falla, diagnosticar -> corregir
  -> re-ejecutar la bateria -> repetir
```

NO se marca completa con:
- Un comando fallando (cualquiera)
- Un test rojo
- Coverage < 80% per-file en archivos modificados
- Una verificacion DB real que devuelve count inesperado

## Parte A — Refactor de tests + grep de huerfanos

### A.1 — Cero referencias a nombres viejos en el codigo no-spec

```bash
# Lista de nombres viejos a buscar
git grep -lE '\b(profile|profile_stats|profile_niches|experiences|experience_bullets|experience_niches|experience_skills|education|education_niches|projects|project_case_studies|project_metrics|project_niches|project_tech_tags|skills|skill_categories|skill_category_skills|skill_category_niches|awards|award_niches|certificates|certificate_niches|languages|language_niches|publications|publication_niches|references|reference_niches|niches|niche_priorities|tech_tags|event_types|translations|contacts|sessions|session_visits|tracking_events)\b' \
  -- '*.py' \
  | grep -v 'alembic/versions/' \
  | grep -v 'docs/diagrams/db-er.mmd' \
  | grep -v 'docs/specs/group-tables-by-domain/'
```

**Esperado**: lista vacia. Cualquier hit es un nombre viejo huerfano
que hay que arreglar (excepto el directorio archivado
`serverless/migrations/_archive/` y los archivos legacy de Alembic
versions, que NO se tocan).

### A.2 — Cero referencias a columnas viejas

```bash
git grep -nE '\b(start_ym|end_ym|awarded_ym|start_year|end_year)\b' \
  -- '*.py' '*.yaml' \
  | grep -v 'alembic/versions/' \
  | grep -v 'docs/specs/'
```

**Esperado**: vacio. Las columnas viejas solo deben aparecer en la
migracion historica (versions/) y la migracion nueva (que las renombra).

### A.3 — Cero references a `'reference'` como entity_type

```bash
git grep -nE "entity_type\s*=\s*['\"]reference['\"]|EntityType\.REFERENCE" \
  -- '*.py' \
  | grep -v 'docs/specs/'
```

**Esperado**: vacio. Solo `'endorsement'` debe aparecer en los lambdas.

### A.4 — Tests viejos eliminados o renombrados

```bash
# tests que mencionen tablas/clases viejas en su nombre o contenido
git grep -nE '\b(References|EducationNiche|ReferenceNiche)\b' \
  -- 'serverless/lambda/**/tests/**'
```

**Esperado**: vacio. Si hay hits, son tests que se renombraron y
necesitan actualizar imports + asserts.

## Parte B — Bateria de comandos reales

Ejecutar EN ORDEN. Si UNO falla, parar, diagnosticar, corregir,
re-ejecutar desde el principio.

### B.1 — Quality gates Python

```bash
# Sintaxis
python -m compileall -q serverless/lambda/

# Lint (devtools y shared)
python devtools/run.py docker lint --module=devtools --env=local
```

### B.2 — Unit tests por lambda + shared

```bash
serverless tests --type=unit --shared
serverless tests --type=unit --lambda=db
serverless tests --type=unit --lambda=stream_processor
serverless tests --type=unit --lambda=contact_form
serverless tests --type=unit --lambda=tracking_pixel
# si existe cv:
serverless tests --type=unit --lambda=cv
```

**Gate**: cero rojos, coverage >= 80% per-file en archivos modificados.

### B.3 — Lint-deps de cada lambda

```bash
python devtools/run.py serverless lint-deps --lambda=db
python devtools/run.py serverless lint-deps --lambda=stream_processor
python devtools/run.py serverless lint-deps --lambda=contact_form
python devtools/run.py serverless lint-deps --lambda=tracking_pixel
```

**Gate**: cero warnings de deps no declaradas o duplicadas.

### B.4 — Migracion idempotente en branch Neon de prueba

```bash
# Crear branch limpia (snapshot del dev pre-migracion)
neonctl branches create --name e2e-verify --parent br-little-glitter-akq7ugv3
export DATABASE_URL=$(neonctl connection-string e2e-verify --role-name neondb_owner)
python devtools/run.py serverless setup-ssm \
  --name=/portfolio/local/neon-url \
  --key-id=alias/portfolio-lambdas --env=local --value-from-stdin <<< "$DATABASE_URL"

# Upgrade
serverless run --stage=local --lambda=db --event=events/migrate.json

# Verificacion DB real post-migrate
psql "$DATABASE_URL" <<SQL
SELECT count(*) FROM information_schema.tables WHERE table_schema='public';
-- esperado: 39 (37 + alembic_version + vis_tracking_events_default)
SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name NOT LIKE 'cv_%' AND table_name NOT LIKE 'vis_%' AND table_name NOT LIKE 'tax_%' AND table_name NOT LIKE 'i18n_%' AND table_name != 'alembic_version';
-- esperado: solo vis_tracking_events_default (particion)
SELECT version_num FROM alembic_version;
-- esperado: <ULID nuevo>
SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname='entity_type') ORDER BY enumsortorder;
-- esperado: incluye 'endorsement', NO incluye 'reference'
SQL

# Downgrade test
serverless run --stage=local --lambda=db --event=events/downgrade.json
psql "$DATABASE_URL" -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'cv_%'"
# esperado: 0 (nombres viejos restaurados)

# Re-upgrade (idempotencia)
serverless run --stage=local --lambda=db --event=events/migrate.json
psql "$DATABASE_URL" -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'cv_%'"
# esperado: 28
```

### B.5 — Seed completo en branch de prueba

```bash
serverless run --stage=local --lambda=db --event=events/seed.json
# Esperado: logs con counts (1 profile, 9 experiences, 4 projects, etc.)

# Verificacion DB real post-seed
psql "$DATABASE_URL" <<SQL
SELECT
  (SELECT count(*) FROM cv_profiles) AS profile,
  (SELECT count(*) FROM cv_experiences) AS exp,
  (SELECT count(*) FROM cv_projects) AS proj,
  (SELECT count(*) FROM cv_endorsements) AS endor,
  (SELECT count(*) FROM cv_skills) AS skills,
  (SELECT count(*) FROM tax_niches) AS niches,
  (SELECT count(*) FROM tax_event_types) AS event_types,
  (SELECT count(*) FROM i18n_translations) AS translations;
-- esperado (basado en data actual de dev):
-- profile=1, exp=9, proj=4, endor=10, skills=99, niches=5, event_types=16, translations>=372

-- Fechas son DATE no varchar
SELECT pg_typeof(started_on) FROM cv_experiences LIMIT 1;
-- esperado: date

-- Slugs poblados
SELECT count(*) FROM cv_skills WHERE slug IS NULL OR slug = '';
-- esperado: 0
SELECT count(*) FROM tax_tech_tags WHERE slug IS NULL OR slug = '';
-- esperado: 0

-- PK fisica activa
INSERT INTO vis_tracking_events (created_at, visit_id, page_id, session_id, received_at)
VALUES (now(), gen_random_uuid(), gen_random_uuid(), 'test-sess', now());
INSERT INTO vis_tracking_events (created_at, visit_id, page_id, session_id, received_at)
SELECT created_at, visit_id, page_id, 'other', now() FROM vis_tracking_events ORDER BY created_at DESC LIMIT 1;
-- esperado: ERROR duplicate key value violates unique constraint "pk_vis_tracking_events"
SQL
```

### B.6 — Integration tests con DB real por lambda

Esta es la parte que el usuario explicitamente pidio. Cada lambda
corre integration y AL FINAL hace SELECT a Neon para verificar
persistencia con los nombres nuevos.

```bash
# Cada uno debe apuntar al branch e2e-verify
export DATABASE_URL=$(neonctl connection-string e2e-verify --role-name neondb_owner)

serverless tests --type=integration --lambda=db
serverless tests --type=integration --lambda=stream_processor
serverless tests --type=integration --lambda=contact_form
serverless tests --type=integration --lambda=tracking_pixel
```

**Gate**: cada test integration termina con assert sobre query `psql`
o `psycopg` directo al branch e2e-verify. Ej:

```python
# tests/integration/test_contact_form_persists_e2e.py
def test_post_persists_to_vis_contacts_e2e(branch_db, lambda_invoker):
    payload = {'name': 'Smoke', 'email': 'smoke@e2e.dev', ...}
    response = lambda_invoker.invoke('contact_form', payload)
    assert response['statusCode'] == 200

    # Verificacion DB real (la clave del requisito)
    with psycopg.connect(branch_db) as conn:
        row = conn.execute(
            "SELECT id, email, session_id FROM vis_contacts WHERE email = %s",
            (payload['email'],)
        ).fetchone()
    assert row is not None
    assert row[1] == 'smoke@e2e.dev'
    assert row[2] is not None  # session_id NOT NULL (AC-5)
```

### B.7 — Coverage check

```bash
serverless tests --type=coverage --lambda=db
serverless tests --type=coverage --lambda=stream_processor
serverless tests --type=coverage --lambda=contact_form
serverless tests --type=coverage --lambda=tracking_pixel
```

**Gate**: cada archivo MODIFICADO en este PR debe tener >= 80%
coverage. Archivos NO modificados no cuentan (baseline preservada).

### B.8 — Cleanup branch de prueba

```bash
neonctl branches delete e2e-verify
```

## Bucle de correccion ("no parar hasta verde")

```text
1. Correr B.1
2. ¿paso? -> seguir con B.2; ¿no? -> diagnosticar, corregir,
   commitear el fix, volver a 1
3. Idem hasta B.8
4. Si B.8 verde -> proceder al commit final 12
```

## Commit final 12 — push + PR

UNA vez TODA la bateria en verde:

```bash
# Eliminar la spec efimera
git rm -r docs/specs/group-tables-by-domain/

git add -A
git commit -m "$(cat <<'EOF'
chore(verify): bateria E2E iterativa + elimina docs/specs/group-tables-by-domain/

(detalle en el mensaje del commit 12 de 10-commits.md)
EOF
)"

# Push + PR
git push -u origin feature/group-tables-by-domain
gh pr create --base dev --head feature/group-tables-by-domain \
  --title "feat(db): group tables by domain (cv_ vis_ tax_ i18n_) + normaliza fechas/slugs/pk" \
  --body "$(cat <<'EOF'
## Problema
1. 37 tablas en `public` sin separador visual entre dominios (CV, visitor, taxonomy, i18n)
2. Inconsistencias: fechas como VARCHAR, falta de slug en skills/tech_tags, sin PK fisica en tracking_events, `references` palabra reservada SQL

## Solucion
1. Prefijo en `__tablename__`: `cv_*` (28), `vis_*` (4), `tax_*` (4), `i18n_*` (1)
2. Normalizacion: DATE para fechas, slug UK en skills/tech_tags, PK fisica en vis_tracking_events, references -> endorsements

## Como probar
- `serverless tests --type=integration` para los 4 lambdas (incluye verificacion DB real)
- Migrate up/down/up en branch Neon de prueba: ver `docs/diagrams/db-er.mmd` (commiteado) como referencia del schema objetivo
- Smoke test post-merge en dev: POST /contact + GET /track + verificacion `psql -c "SELECT count(*) FROM vis_contacts ..."`

## TODO (no bloquea merge)
- Aplicar Fase 5 (provision stage/prod desde cero) en los PRs de promocion
- Documentar en `.claude/rules/neon-management.md` el nuevo estado de las 3 branches Neon
EOF
)"
```

## Despues de mergear el PR

1. CI corre `migrate-db` -> `deploy-lambdas` en dev. Verificar logs.
2. Smoke test en dev: form de contacto + tracking pixel + queries DB.
3. Promover dev -> stage con PR + ejecutar Fase 5 paso 5.1.
4. Promover stage -> main + ejecutar Fase 5 paso 5.2.

## Cleanup post-PR mergeado

- `docs/specs/group-tables-by-domain/` ya eliminada por el commit 12
- `docs/diagrams/db-er.mmd` PERMANECE (es estado actualizado, no
  spec efimera)
- Branches worktree (`worktree/db`, `worktree/stream-processor`, ...)
  borradas localmente con `git branch -d` y remotamente con `git push
  origin --delete worktree/X`
