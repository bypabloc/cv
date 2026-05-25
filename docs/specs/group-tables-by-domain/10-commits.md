# 10 — Commits

[README](README.md) | [09-fase-provision](09-fase-provision-stage-prod.md) |
**10-commits** | [11-paralelizacion](11-paralelizacion-worktrees.md)

## Regla por commit (OBLIGATORIA)

Cada commit del plan ejecuta su verificacion incremental **ANTES** de
commitear. Si la verificacion falla, NO se commitea; se corrige y se
re-ejecuta la suite hasta verde. Esto enforce que el repo esta verde
en CADA commit del historial, no solo al final.

Comandos canonicos por tipo:

- Modelos / shared: `python -m compileall -q serverless/lambda/shared/ &&
  serverless tests --type=unit --shared`
- Migracion: `alembic upgrade head && alembic downgrade -1 && alembic
  upgrade head` (en branch Neon de prueba) + verificacion DB real con
  `psql "$DATABASE_URL" -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"`
- Lambda especifico: `serverless tests --type=unit --lambda=<X> &&
  serverless tests --type=integration --lambda=<X>` + queries
  `psql` post-feature segun Fase 4
- Seeds: `serverless tests --type=integration --lambda=db` + verificar
  fechas son `date` y slugs no nulos en Neon

## Listado de commits

### Commit 1 — `docs(specs): inicia plan group-tables-by-domain`

**Archivos**: `docs/specs/group-tables-by-domain/` (12 .md + README) +
`docs/diagrams/db-er.mmd` (actualizado al estado objetivo)

**AC**: ninguno directo (plan + diagrama de referencia)

**Verificacion**:
```bash
pnpm dlx @mermaid-js/mermaid-cli@latest \
  -i docs/diagrams/db-er.mmd -o /tmp/db-er.svg && rm /tmp/db-er.svg
# diagrama valido
```

**Mensaje**:
```
docs(specs): inicia plan group-tables-by-domain

- Crea docs/specs/group-tables-by-domain/ con 13 archivos (README + 12 secciones)
- Actualiza docs/diagrams/db-er.mmd al estado objetivo (37 tablas prefijadas, fechas DATE, slugs, PK fisica)
- Documenta 22 decisiones consolidadas tras 4 rondas de Q&A
- Anexa mapeo exhaustivo de 1000+ ocurrencias a renombrar (13-mapeo-usos-modelos.md)
```

---

### Commit 2 — `refactor(shared/db): reorganiza modelos en subcarpetas cv/visitor/taxonomy/i18n`

**Archivos**: 18 nuevos en `shared/db/models/{cv,visitor,taxonomy,i18n}/`
+ 11 viejos eliminados + `__init__.py` raiz actualizado.

Los `__tablename__` siguen siendo los **viejos** (no cambia DB aun); el
commit solo refactoriza estructura Python.

**AC**: AC-8 parcial (imports siguen funcionando)

**Verificacion**:
```bash
python -m compileall -q serverless/lambda/shared/
python -c "from shared.db.models import Profile; assert Profile.__tablename__ == 'profile'"
serverless tests --type=unit --shared
```

**Mensaje**:
```
refactor(shared/db): reorganiza modelos en subcarpetas cv/visitor/taxonomy/i18n

- Crea shared/db/models/{cv,visitor,taxonomy,i18n}/ con un archivo por agrupacion logica
- Mueve 30+ clases preservando nombre (Profile, Contact, Niche, Translation, etc.)
- Elimina los 11 archivos viejos en shared/db/models/*.py
- __init__.py raiz re-exporta todo para preservar API publica (from shared.db.models import X)
- __tablename__ sin cambios (DB intacta, solo refactor Python)
```

---

### Commit 3 — `feat(shared/db): aplica prefijos cv_/vis_/tax_/i18n_ + normaliza columnas + slugs + PK fisica`

**Archivos**: cada archivo nuevo de `shared/db/models/{cv,visitor,
taxonomy,i18n}/*.py` se edita para:
- Cambiar `__tablename__` al nuevo nombre con prefijo
- Renombrar columnas (started_on, ended_on, awarded_on, display_order)
- Agregar slug en Skill y TechTag
- Agregar PrimaryKeyConstraint en TrackingEvent
- Renombrar `References` -> `Endorsement`, `ReferenceNiche` -> `EndorsementNiche`
- Renombrar `Education` -> `EducationEntry`, `EducationNiche` -> `EducationEntryNiche`

**AC**: AC-1, AC-2 (modelo), AC-4 (modelo), AC-9 (clases), AC-10
(declarativo), AC-11 (modelo)

**Verificacion** (sin DB todavia):
```bash
serverless tests --type=unit --shared
python -c "from shared.db.models import Profile, Endorsement, EducationEntry; \
           assert Profile.__tablename__ == 'cv_profiles'; \
           assert Endorsement.__tablename__ == 'cv_endorsements'; \
           assert EducationEntry.__tablename__ == 'cv_education_entries'"
```

**Mensaje**:
```
feat(shared/db): aplica prefijos cv_/vis_/tax_/i18n_ + normaliza columnas + slugs + PK fisica

- 37 tablas con prefijo de dominio (__tablename__ en cada modelo)
- Renames de entidad: profile->cv_profiles, education->cv_education_entries, references->cv_endorsements
- Fechas como DATE: started_on/ended_on (Experience), awarded_on (Award), started_on/ended_on (EducationEntry)
- Slugs UK: cv_skills.slug, tax_tech_tags.slug
- tax_niches.position -> tax_niches.display_order
- PrimaryKeyConstraint fisica en vis_tracking_events (created_at, visit_id, page_id)
- Junctions cascade: education_id -> education_entry_id, reference_id -> endorsement_id
- ENUM entity_type: 'reference' -> 'endorsement'
```

---

### Commit 4 — `feat(shared/db/alembic): nueva migracion group_tables_by_domain`

**Archivos**: `shared/db/alembic/versions/<ULID>_group_tables_by_domain.py`
+ `_init_schema_extras.py` actualizado (trigger + event_types).

**AC**: AC-1, AC-2, AC-4, AC-9, AC-10, AC-11 (Aplicados en DB)

**Verificacion** (en branch Neon de prueba):
```bash
neonctl branches create --name test-rename --parent br-little-glitter-akq7ugv3
export DATABASE_URL=<branch-url>

# Pre-migrate: schema viejo
psql "$DATABASE_URL" -c "\dt" | head -5

# Upgrade
serverless run --stage=local --lambda=db --event=events/migrate.json

# Verificacion DB real
psql "$DATABASE_URL" <<SQL
SELECT count(*) FROM information_schema.tables WHERE table_schema='public';
-- esperado: 39
SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'cv_%';
-- esperado: 28
SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'vis_%';
-- esperado: 4
SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'tax_%';
-- esperado: 4
SELECT pg_typeof(started_on) FROM cv_experiences LIMIT 1;
-- esperado: date
SELECT version_num FROM alembic_version;
-- esperado: <ULID>
SQL

# Downgrade test
serverless run --stage=local --lambda=db --event=events/downgrade.json
psql "$DATABASE_URL" -c "\dt" | head -5  # nombres viejos restaurados
serverless run --stage=local --lambda=db --event=events/migrate.json  # re-upgrade

# Cleanup
neonctl branches delete test-rename
```

**Mensaje**:
```
feat(shared/db/alembic): nueva migracion group_tables_by_domain

- 37 op.rename_table() con prefijos cv_/vis_/tax_/i18n_
- ALTER COLUMN para fechas: VARCHAR(7) -> DATE en cv_experiences, cv_awards, cv_education_entries
- Backfill + add_column slug en cv_skills y tax_tech_tags
- ALTER COLUMN position -> display_order en tax_niches
- CREATE PRIMARY KEY en vis_tracking_events (created_at, visit_id, page_id)
- ALTER TYPE entity_type RENAME VALUE 'reference' TO 'endorsement'
- Regenera trigger assert_entity_exists con nueva lookup
- downgrade() reversible (probado en branch Neon de prueba)
```

---

### Commit 5 — `refactor(services/db): seed_service usa helpers, fechas DATE, slugs, endorsements`

**Archivos**: `shared/db/seed_helpers.py` (nuevo), `services/db/core/services/seed_service.py`,
`services/db/core/seeds/data/references/ -> endorsements/`.

**AC**: AC-2, AC-4 (seeds), AC-9 (entity_type)

**Verificacion** + DB real post-seed (ver Fase 3 Paso 3.4).

**Mensaje**:
```
refactor(services/db): seed_service usa helpers, fechas DATE, slugs, endorsements

- Nuevo: shared/db/seed_helpers.py con _parse_ym() y _to_slug()
- seed_service convierte YAMLs '2024-01' a date(2024, 1, 1)
- Genera slugs para cv_skills y tax_tech_tags via _to_slug()
- entity_type='endorsement' en translations y niche_priorities
- git mv seeds/data/references/ -> seeds/data/endorsements/
```

---

### Commits 6-9 — `refactor(services/<X>): actualiza imports y queries a tablas renombradas`

Un commit por lambda downstream. Verificacion en cada uno: unit +
integration + queries DB reales post-feature.

- **Commit 6**: `services/db` (controllers, cv_repository, repository)
- **Commit 7**: `services/stream_processor`
- **Commit 8**: `services/contact_form`
- **Commit 9**: `services/tracking_pixel`
- **Commit 10**: `services/cv` (si existe — checkear con `ls
  serverless/lambda/services/cv 2>/dev/null`)

Cada mensaje:
```
refactor(services/<X>): actualiza imports y queries a tablas renombradas

- Imports apuntan a shared.db.models.{cv,visitor,taxonomy,i18n}
- Queries SQL raw / ORM usan cv_*/vis_*/tax_*/i18n_*
- Integration test agregado: verificacion DB real con psycopg post-feature
- AC verificados: AC-<n>, AC-<m>
```

---

### Commit 11 — `test(integration): contraste DB real post-feature en los 4 lambdas`

**Archivos**: tests integration nuevos en cada lambda + fixtures
compartidas (`tests/integration/_fixtures/db_branch.py` para crear/
destruir branch Neon).

**AC**: AC-12 (tests verdes con coverage 80%+)

**Verificacion**:
```bash
serverless tests --type=integration --lambda=db
serverless tests --type=integration --lambda=stream_processor
serverless tests --type=integration --lambda=contact_form
serverless tests --type=integration --lambda=tracking_pixel
# todos en verde
```

**Mensaje**:
```
test(integration): contraste DB real post-feature en los 4 lambdas

- Cada integration test ahora termina con SELECT directo a Neon via psycopg
- Verifica que la fila persistio en la tabla con prefijo correcto (vis_*, cv_*)
- Fixture compartida: db_branch crea/destruye branch Neon por test session
- Coverage >= 80% per-file mantenida
```

---

### Commit 12 — `chore(verify): bateria E2E iterativa + elimina docs/specs/group-tables-by-domain/`

**Archivos**: cualquier fix final detectado por la bateria E2E +
`git rm -r docs/specs/group-tables-by-domain/`.

**AC**: AC-12 + cierre de plan.

**Verificacion**: la bateria E2E completa de `12-verificacion-e2e.md`
TODA en verde.

**Mensaje**:
```
chore(verify): bateria E2E iterativa + elimina docs/specs/group-tables-by-domain/

- Bateria completa de la seccion 12 corrida en verde:
  * shared tests (unit + integration)
  * 4 lambdas: unit + integration + verificacion DB real
  * migrate up + down + up en branch Neon de prueba
  * coverage >= 80% per-file en archivos modificados
- Eliminada la spec efimera (decisiones quedan en git log + PR mergeado)
- Diagrama docs/diagrams/db-er.mmd preservado (es permanente)
```

---

## Despues del commit 12

1. `git push origin feature/group-tables-by-domain` (recien aqui, NO
   antes — regla del plan-format).
2. `gh pr create --base dev --head feature/group-tables-by-domain`
   con body apuntando a la spec mergeada (link al SHA del commit 1).
3. CI corre `migrate-db` -> `deploy-lambdas` matrix en dev.
4. Smoke test en dev manual.
5. Si OK: PR `dev -> stage`, ejecutar Fase 5 paso 5.1.
6. Si OK en stage: PR `stage -> main`, ejecutar Fase 5 paso 5.2.

## Resumen

- **12 commits**, cada uno deja el repo en verde
- **1 solo PR a dev** (`feature/group-tables-by-domain -> dev`)
- **2 PRs de promocion** (dev->stage, stage->main) — sin codigo, solo
  merge commits del CI
