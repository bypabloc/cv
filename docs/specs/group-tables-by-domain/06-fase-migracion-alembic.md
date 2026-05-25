# 06 — Fase 2: Migracion Alembic

[README](README.md) | [05-fase-modelos](05-fase-modelos-reorganizacion.md) |
**06-fase-migracion** | [07-fase-seeds](07-fase-seeds-update.md)

## Objetivo

Generar UNA migracion Alembic que renombre las 37 tablas, normalice
columnas, agregue PK fisica, regenere el trigger polimorfico y rote el
ENUM `entity_type`. Toda la operacion en una sola transaccion (donde PG
lo permita) para garantizar atomicidad.

## Pre-requisitos

- Fase 1 completa (modelos apuntan a las tablas nuevas, pero la DB
  todavia no se ha migrado).
- Branch Neon de prueba creada para validar:
  ```bash
  neonctl branches create --name test-group-tables-by-domain \
    --parent br-little-glitter-akq7ugv3
  ```
  (parent es el branch `dev`).
- `DATABASE_URL` apunta al branch de prueba para correr `alembic` local.

## Pasos

### Paso 2.1 — Crear archivo de migracion

```bash
cd serverless/lambda
DATABASE_URL=<branch-de-prueba> \
  .venv/bin/alembic -c shared/db/alembic.ini revision \
  --message "group_tables_by_domain" --rev-id "<ULID corto>"
```

Resultado: `serverless/lambda/shared/db/alembic/versions/<ULID>_group_tables_by_domain.py`
con `upgrade()` y `downgrade()` vacios.

### Paso 2.2 — Escribir `upgrade()`

Orden importante:

#### 1. Rename de tablas (37 ALTER TABLE)

```python
def upgrade() -> None:
    # CV (28 tablas) — orden: padres primero, luego junctions, luego auxiliares
    op.rename_table('profile', 'cv_profiles')
    op.rename_table('profile_stats', 'cv_profile_stats')
    op.rename_table('profile_niches', 'cv_profile_niches')
    op.rename_table('experiences', 'cv_experiences')
    op.rename_table('experience_bullets', 'cv_experience_bullets')
    op.rename_table('experience_niches', 'cv_experience_niches')
    op.rename_table('experience_skills', 'cv_experience_skills')
    op.rename_table('education', 'cv_education_entries')
    op.rename_table('education_niches', 'cv_education_entry_niches')
    op.rename_table('projects', 'cv_projects')
    op.rename_table('project_case_studies', 'cv_project_case_studies')
    op.rename_table('project_metrics', 'cv_project_metrics')
    op.rename_table('project_niches', 'cv_project_niches')
    op.rename_table('project_tech_tags', 'cv_project_tech_tags')
    op.rename_table('skills', 'cv_skills')
    op.rename_table('skill_categories', 'cv_skill_categories')
    op.rename_table('skill_category_skills', 'cv_skill_category_skills')
    op.rename_table('skill_category_niches', 'cv_skill_category_niches')
    op.rename_table('awards', 'cv_awards')
    op.rename_table('award_niches', 'cv_award_niches')
    op.rename_table('certificates', 'cv_certificates')
    op.rename_table('certificate_niches', 'cv_certificate_niches')
    op.rename_table('languages', 'cv_languages')
    op.rename_table('language_niches', 'cv_language_niches')
    op.rename_table('publications', 'cv_publications')
    op.rename_table('publication_niches', 'cv_publication_niches')
    op.rename_table('references', 'cv_endorsements')
    op.rename_table('reference_niches', 'cv_endorsement_niches')
    # Visitor (4)
    op.rename_table('contacts', 'vis_contacts')
    op.rename_table('sessions', 'vis_sessions')
    op.rename_table('session_visits', 'vis_session_visits')
    op.rename_table('tracking_events', 'vis_tracking_events')
    # Taxonomy (4)
    op.rename_table('niches', 'tax_niches')
    op.rename_table('niche_priorities', 'tax_niche_priorities')
    op.rename_table('tech_tags', 'tax_tech_tags')
    op.rename_table('event_types', 'tax_event_types')
    # i18n (1)
    op.rename_table('translations', 'i18n_translations')
    # Particion fisica (tabla hija de la particionada)
    op.execute(
        'ALTER TABLE tracking_events_default '
        'RENAME TO vis_tracking_events_default'
    )
```

#### 2. Rename de columnas FK que cambiaron de tabla padre

```python
    op.alter_column(
        'cv_education_entry_niches',
        'education_id',
        new_column_name='education_entry_id',
    )
    op.alter_column(
        'cv_endorsement_niches',
        'reference_id',
        new_column_name='endorsement_id',
    )
```

#### 3. Normalizacion de fechas (VARCHAR -> DATE)

```python
    # cv_experiences
    op.execute("ALTER TABLE cv_experiences DROP CONSTRAINT IF EXISTS ck_experiences_start_ym")
    op.execute("ALTER TABLE cv_experiences DROP CONSTRAINT IF EXISTS ck_experiences_end_ym")
    op.execute("""
        ALTER TABLE cv_experiences
        ALTER COLUMN start_ym TYPE date USING (start_ym || '-01')::date,
        ALTER COLUMN end_ym   TYPE date USING (CASE WHEN end_ym IS NULL THEN NULL ELSE (end_ym || '-01')::date END)
    """)
    op.alter_column('cv_experiences', 'start_ym', new_column_name='started_on')
    op.alter_column('cv_experiences', 'end_ym',   new_column_name='ended_on')

    # cv_awards
    op.execute("ALTER TABLE cv_awards DROP CONSTRAINT IF EXISTS ck_awards_awarded_ym")
    op.execute("""
        ALTER TABLE cv_awards
        ALTER COLUMN awarded_ym TYPE date USING (awarded_ym || '-01')::date
    """)
    op.alter_column('cv_awards', 'awarded_ym', new_column_name='awarded_on')

    # cv_education_entries
    op.execute("""
        ALTER TABLE cv_education_entries
        ALTER COLUMN start_year TYPE date USING (
            CASE WHEN start_year ~ '^\\d{4}-\\d{2}-\\d{2}$' THEN start_year::date
                 WHEN start_year ~ '^\\d{4}-\\d{2}$' THEN (start_year || '-01')::date
                 WHEN start_year ~ '^\\d{4}$' THEN (start_year || '-01-01')::date
                 ELSE NULL END
        ),
        ALTER COLUMN end_year TYPE date USING (
            CASE WHEN end_year IS NULL THEN NULL
                 WHEN end_year ~ '^\\d{4}-\\d{2}-\\d{2}$' THEN end_year::date
                 WHEN end_year ~ '^\\d{4}-\\d{2}$' THEN (end_year || '-01')::date
                 WHEN end_year ~ '^\\d{4}$' THEN (end_year || '-01-01')::date
                 ELSE NULL END
        )
    """)
    op.alter_column('cv_education_entries', 'start_year', new_column_name='started_on')
    op.alter_column('cv_education_entries', 'end_year',   new_column_name='ended_on')
```

#### 4. Slugs nuevos en cv_skills y tax_tech_tags

```python
    # Agregar slug nullable, backfill, set NOT NULL + UNIQUE
    op.add_column('cv_skills', sa.Column('slug', sa.String(120), nullable=True))
    op.execute("""
        UPDATE cv_skills
        SET slug = lower(regexp_replace(name, '[^a-z0-9]+', '-', 'gi'))
    """)
    op.execute(
        "UPDATE cv_skills SET slug = regexp_replace(slug, '(^-|-$)', '', 'g')"
    )
    op.alter_column('cv_skills', 'slug', nullable=False)
    op.create_unique_constraint('uq_cv_skills_slug', 'cv_skills', ['slug'])

    op.add_column('tax_tech_tags', sa.Column('slug', sa.String(120), nullable=True))
    op.execute("""
        UPDATE tax_tech_tags
        SET slug = lower(regexp_replace(name, '[^a-z0-9]+', '-', 'gi'))
    """)
    op.execute(
        "UPDATE tax_tech_tags SET slug = regexp_replace(slug, '(^-|-$)', '', 'g')"
    )
    op.alter_column('tax_tech_tags', 'slug', nullable=False)
    op.create_unique_constraint('uq_tax_tech_tags_slug', 'tax_tech_tags', ['slug'])
```

#### 5. tax_niches.position -> display_order

```python
    op.alter_column('tax_niches', 'position', new_column_name='display_order')
```

#### 6. PK fisica en vis_tracking_events

```python
    op.create_primary_key(
        'pk_vis_tracking_events',
        'vis_tracking_events',
        ['created_at', 'visit_id', 'page_id'],
    )
```

#### 7. ENUM entity_type: 'reference' -> 'endorsement'

```python
    op.execute("ALTER TYPE entity_type RENAME VALUE 'reference' TO 'endorsement'")
```

#### 8. Trigger polimorfico actualizado

```python
    op.execute("""
        CREATE OR REPLACE FUNCTION assert_entity_exists(
            p_entity_type entity_type,
            p_entity_id uuid
        ) RETURNS boolean AS $$
        DECLARE
            v_exists boolean;
            v_table text;
        BEGIN
            v_table := CASE p_entity_type
                WHEN 'profile' THEN 'cv_profiles'
                WHEN 'experience' THEN 'cv_experiences'
                WHEN 'experience_bullet' THEN 'cv_experience_bullets'
                WHEN 'project' THEN 'cv_projects'
                WHEN 'project_case_study' THEN 'cv_project_case_studies'
                WHEN 'education' THEN 'cv_education_entries'
                WHEN 'award' THEN 'cv_awards'
                WHEN 'certificate' THEN 'cv_certificates'
                WHEN 'language' THEN 'cv_languages'
                WHEN 'publication' THEN 'cv_publications'
                WHEN 'endorsement' THEN 'cv_endorsements'
                WHEN 'skill_category' THEN 'cv_skill_categories'
            END;
            EXECUTE format('SELECT EXISTS (SELECT 1 FROM %I WHERE id = $1)', v_table)
                INTO v_exists USING p_entity_id;
            RETURN v_exists;
        END;
        $$ LANGUAGE plpgsql;
    """)
```

#### 9. Regenerar constraints con nuevos nombres

Alembic genera nombres de constraints segun la naming_convention de
`MetaData`. Como el rename de tablas no rebautiza los constraints
automaticamente, hay que dropear y recrear los importantes para
mantener la convencion `pk_<table>`, `fk_<table>_<col>_<ref>`, etc.
Plan: opcional — los constraints viejos siguen siendo validos
funcionalmente, solo el nombre queda desactualizado. **Decision**: NO
renombrar constraints en esta migracion (es trabajo cosmetico y la
migracion ya es enorme). Documentar como deuda tecnica en
`12-verificacion-e2e.md`.

### Paso 2.3 — Escribir `downgrade()`

Reverso exacto de cada operacion del upgrade, en orden inverso. La
migracion debe ser **completamente reversible**.

### Paso 2.4 — Probar en branch Neon de prueba

```bash
# Apuntar al branch
export DATABASE_URL="postgresql://...test-group-tables-by-domain..."

# 1. upgrade
serverless run --stage=local --lambda=db --event=events/migrate.json

# 2. validar schema
psql "$DATABASE_URL" -c "\dt" | head -50    # 37 tablas + alembic_version + tracking_events_default partition
psql "$DATABASE_URL" -c "SELECT version_num FROM alembic_version"

# 3. downgrade
psql ... # o evento custom con target='-1'

# 4. validar schema viejo restaurado
psql "$DATABASE_URL" -c "\dt"               # nombres viejos de vuelta

# 5. re-upgrade (validar idempotencia)
serverless run --stage=local --lambda=db --event=events/migrate.json
```

Si `upgrade-downgrade-upgrade` produce el mismo schema final, la
migracion es solida.

### Paso 2.5 — Eliminar branch de prueba

```bash
neonctl branches delete test-group-tables-by-domain
```

## Definition of done (Fase 2)

- [ ] Archivo `<ULID>_group_tables_by_domain.py` creado en
  `alembic/versions/`
- [ ] `upgrade()` cubre: 37 renames + 4 columnas fecha + 2 slugs + 1
  display_order + 1 PK fisica + 1 ENUM value rename + 1 trigger update
- [ ] `downgrade()` es reversible exacto (verificado en branch de
  prueba)
- [ ] Tests integration nuevos pasan en branch de prueba
- [ ] Branch de prueba eliminado
- [ ] La migracion NO se aplica todavia a dev (queda lista para CI run
  del PR)

## Riesgos

- **Transaccion gigante**: 37 ALTERs + 4 type-changes + backfills.
  Posible timeout en bases con mucha data. Mitigacion: dev tiene 372
  filas en la tabla mas grande (translations), peso total bajo. Stage
  y prod se rehacen desde cero (Fase 5).
- **`ALTER TYPE entity_type RENAME VALUE`** es no-transaccional en
  algunas versiones PG; PG18 lo soporta. Verificar en branch de prueba.
- **Trigger PL/pgSQL**: si tiene cache de plan, podria fallar la
  primera invocacion tras el rename. Mitigar con `DISCARD PLANS` o
  recreacion completa del trigger.
