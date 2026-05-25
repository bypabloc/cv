# 04 — Archivos Afectados

[README](README.md) | [03-tests](03-tests-requeridos.md) |
**04-archivos** | [05-fase-modelos](05-fase-modelos-reorganizacion.md)

Cada archivo lleva un comando de verificacion explicito (convierte la
lista en checklist ejecutable).

## Crear

### Subcarpetas de modelos

- `serverless/lambda/shared/db/models/cv/__init__.py` — re-exports de CV (Profile, ProfileStats, ProfileNiche, Experience, ExperienceBullet, ExperienceNiche, ExperienceSkill, EducationEntry, EducationEntryNiche, Project, ProjectCaseStudy, ProjectMetric, ProjectNiche, ProjectTechTag, Skill, SkillCategory, SkillCategorySkill, SkillCategoryNiche, Award, AwardNiche, Certificate, CertificateNiche, Language, LanguageNiche, Publication, PublicationNiche, Endorsement, EndorsementNiche)
  - Verificar: `python -c "from shared.db.models.cv import Profile; assert Profile.__tablename__ == 'cv_profiles'"`
- `serverless/lambda/shared/db/models/cv/profile.py` — clases Profile, ProfileStats, ProfileNiche
- `serverless/lambda/shared/db/models/cv/experience.py` — Experience, ExperienceBullet, ExperienceNiche, ExperienceSkill
- `serverless/lambda/shared/db/models/cv/education.py` — EducationEntry, EducationEntryNiche
- `serverless/lambda/shared/db/models/cv/project.py` — Project, ProjectCaseStudy, ProjectMetric, ProjectNiche, ProjectTechTag
- `serverless/lambda/shared/db/models/cv/skill.py` — Skill, SkillCategory, SkillCategorySkill, SkillCategoryNiche
- `serverless/lambda/shared/db/models/cv/cv_entity.py` — Award, AwardNiche, Certificate, CertificateNiche, Language, LanguageNiche, Publication, PublicationNiche, Endorsement, EndorsementNiche
- `serverless/lambda/shared/db/models/visitor/__init__.py` — re-exports
- `serverless/lambda/shared/db/models/visitor/contact.py` — Contact
- `serverless/lambda/shared/db/models/visitor/session.py` — Session
- `serverless/lambda/shared/db/models/visitor/session_visit.py` — SessionVisit
- `serverless/lambda/shared/db/models/visitor/tracking.py` — TrackingEvent
- `serverless/lambda/shared/db/models/taxonomy/__init__.py` — re-exports
- `serverless/lambda/shared/db/models/taxonomy/catalog.py` — Niche, TechTag
- `serverless/lambda/shared/db/models/taxonomy/priority.py` — NichePriority
- `serverless/lambda/shared/db/models/taxonomy/event_type.py` — EventType
- `serverless/lambda/shared/db/models/i18n/__init__.py` — re-exports
- `serverless/lambda/shared/db/models/i18n/translation.py` — Translation
  - Verificar (todos): `python -m compileall -q serverless/lambda/shared/db/models/`

### Migracion Alembic

- `serverless/lambda/shared/db/alembic/versions/<ULID>_group_tables_by_domain.py` — la migracion mas grande del proyecto:
  - 37 `op.rename_table(old, new)`
  - 5 `op.alter_column(...)` para fechas (`experiences.start_ym -> started_on`, etc.)
  - 2 `op.add_column(...)` para slugs (`cv_skills.slug`, `tax_tech_tags.slug`)
  - 1 backfill SQL para slugs (UPDATE cv_skills SET slug = lower(regexp_replace(name, '[^a-z0-9]+', '-', 'gi')) ...) + posterior NOT NULL
  - 1 `op.alter_column` para `tax_niches.position -> display_order`
  - 1 `op.drop_constraint` + `op.create_primary_key` para `vis_tracking_events`
  - 1 `op.execute("ALTER TYPE entity_type RENAME VALUE 'reference' TO 'endorsement'")` (PG-native, requiere PG 10+)
  - 1 `op.execute(...)` para actualizar el trigger `assert_entity_exists` con la nueva lookup
  - 1 rename de la particion default `tracking_events_default -> vis_tracking_events_default`
  - `downgrade()` reversible exacto
  - Verificar: dentro de branch Neon de prueba, `alembic upgrade head && alembic downgrade -1 && alembic upgrade head` retorna estado consistente

### Helpers nuevos

- `serverless/lambda/shared/db/seed_helpers.py` — `_parse_ym()` + `_to_slug()`
  - Verificar: `pytest serverless/lambda/shared/tests/db/test_seed_helpers.py`

### Tests nuevos

- `serverless/lambda/shared/tests/db/test_seed_helpers.py`
- `serverless/lambda/shared/tests/db/models/cv/test_profile_tablenames.py`
- `serverless/lambda/shared/tests/db/models/cv/test_endorsement_rename.py`
- `serverless/lambda/shared/tests/db/models/cv/test_experience_dates.py`
- `serverless/lambda/shared/tests/db/models/cv/test_skill_has_slug.py`
- `serverless/lambda/shared/tests/db/models/visitor/test_tracking_pk.py`
- `serverless/lambda/shared/tests/db/models/taxonomy/test_niche_display_order.py`
- `serverless/lambda/services/db/tests/integration/test_migrate_renames_all_tables_e2e.py`
- `serverless/lambda/services/db/tests/integration/test_migrate_downgrade_e2e.py`
- `serverless/lambda/services/db/tests/integration/test_seed_dates_as_date_e2e.py`
- `serverless/lambda/services/db/tests/integration/test_seed_slugs_e2e.py`
- `serverless/lambda/services/db/tests/integration/test_enum_endorsement_value_e2e.py`
- `serverless/lambda/services/db/tests/integration/test_tracking_pk_rejects_duplicate_e2e.py`
- `serverless/lambda/services/stream_processor/tests/integration/test_writes_to_vis_tables_e2e.py`
- `serverless/lambda/services/contact_form/tests/integration/test_persist_vis_contacts_e2e.py`
- `serverless/lambda/services/tracking_pixel/tests/integration/test_persist_vis_tracking_e2e.py`
  - Verificar (todos): `serverless tests --type=integration --lambda=<X>` por cada lambda + `--shared`

## Modificar

### Modelos viejos (eliminar tras migracion)

Los 12 archivos en `serverless/lambda/shared/db/models/` se vacian
quedando solo re-exports compat-ibles desde las nuevas subcarpetas
durante la migracion. **Despues del PR mergeado se eliminan**. Para
evitar dead-code temporal:

- `serverless/lambda/shared/db/models/__init__.py` — actualizar imports a las subcarpetas nuevas; mantener API publica identica (`from shared.db.models import Profile` debe seguir funcionando)
  - Verificar: `grep -r "from shared.db.models import" serverless/lambda/ | wc -l` antes y despues coincide; cero cambios en call-sites
- `serverless/lambda/shared/db/models/catalog.py` — borrar (clases migradas a `taxonomy/catalog.py`)
- `serverless/lambda/shared/db/models/contact.py` — borrar
- `serverless/lambda/shared/db/models/cv_entities.py` — borrar
- `serverless/lambda/shared/db/models/experience.py` — borrar
- `serverless/lambda/shared/db/models/junctions.py` — borrar (cada junction se mueve al archivo de su entidad principal)
- `serverless/lambda/shared/db/models/profile.py` — borrar
- `serverless/lambda/shared/db/models/project.py` — borrar
- `serverless/lambda/shared/db/models/session.py` — borrar
- `serverless/lambda/shared/db/models/session_visit.py` — borrar
- `serverless/lambda/shared/db/models/tracking.py` — borrar
- `serverless/lambda/shared/db/models/translations.py` — borrar
  - Verificar: `python -m compileall -q serverless/lambda/shared/`

### Schema extras

- `serverless/lambda/shared/db/alembic/_init_schema_extras.py` — actualizar el seed de `event_types` para usar el nuevo nombre `tax_event_types`; actualizar el trigger `assert_entity_exists` lookup
  - Verificar: la nueva migracion incluye `op.execute(...)` para refrescar el cuerpo del trigger

### Seed service

- `serverless/lambda/services/db/core/services/seed_service.py` — importar `_parse_ym` y `_to_slug` desde `shared.db.seed_helpers`; usar `cv_endorsements` en vez de `references`; convertir todas las fechas YAML; deduplicar skills con slug; idem tech_tags
  - Verificar: `serverless tests --type=integration --lambda=db --filter test_seed`

### Repositorios

- `serverless/lambda/shared/db/cv_repository.py` — actualizar queries que mencionen tablas/columnas viejas (especialmente `references` -> `cv_endorsements`, `position` -> `display_order`, fechas)
  - Verificar: `grep -E "(references|position|start_ym|awarded_ym|start_year)" serverless/lambda/shared/db/cv_repository.py` no encuentra ocurrencias
- `serverless/lambda/shared/db/repository.py` — idem
  - Verificar: idem

### Lambdas downstream

- `serverless/lambda/services/stream_processor/core/services/*.py` — imports + queries
  - Verificar: `serverless tests --type=integration --lambda=stream_processor`
- `serverless/lambda/services/contact_form/core/services/*.py` — idem
  - Verificar: `serverless tests --type=integration --lambda=contact_form`
- `serverless/lambda/services/tracking_pixel/core/services/*.py` — idem
  - Verificar: `serverless tests --type=integration --lambda=tracking_pixel`

### Tests existentes (~30 archivos)

Lista completa: ver [13-mapeo-usos-modelos.md](13-mapeo-usos-modelos.md)
filtrando por seccion de cada modelo. Tambien re-ejecutable con:

```bash
git grep -lE '\b(profile|experiences|projects|contacts|sessions|tracking_events|niches|tech_tags|translations|event_types|skills|skill_categories|references|education|reference_niches|education_niches)\b' \
  -- 'serverless/lambda/**/tests/**'
```

Cada uno se actualiza con el nuevo nombre/columna. Verificar
individualmente con su pytest.

## Mapeo exhaustivo (anexo)

El archivo [13-mapeo-usos-modelos.md](13-mapeo-usos-modelos.md) lista
**TODAS las ocurrencias** de cada tabla, clase Python y columna a
renombrar — 999 lineas, ~1500 hits clasificados por fase (F1 modelos,
F2 alembic, F3 seeds, F4 lambdas). Es la fuente de verdad operativa
para no perder ninguna referencia al ejecutar el plan.

Top hot-spots por archivo (los con mas hits):

1. `shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py` (138)
2. `shared/db/alembic/versions/d4e5f6a7b8c9_introduce_sessions_visits.py` (111)
3. `shared/db/cv_repository.py` (107)
4. `services/db/core/services/seed_service.py` (82)
5. `shared/db/models/junctions.py` (51)
6. `shared/db/models/cv_entities.py` (34)
7. `shared/db/models/__init__.py` (26)
8. `shared/db/repository.py` (25)
9. `shared/db/alembic/_init_schema_extras.py` (23)
10. `shared/db/models/{profile,project,tracking}.py` (~20 c/u)
11. `services/contact_form/core/services/contact_service.py` (18)

Los archivos en `alembic/versions/` (top 1, 2, 13, 14) son **legacy
inmutables** — NO se editan. Sus referencias a nombres viejos son
correctas porque representan el estado historico del schema antes del
rename.

## Eliminar

- `serverless/lambda/shared/db/models/{catalog,contact,cv_entities,experience,junctions,profile,project,session,session_visit,tracking,translations}.py` — 11 archivos viejos (ver "Modificar" arriba; primero re-exports, despues del PR mergeado se borran)
  - Verificar: `ls serverless/lambda/shared/db/models/` retorna solo las 4 subcarpetas + `__init__.py`
- `docs/specs/group-tables-by-domain/` — la carpeta del plan, en el ULTIMO commit (ver `12-verificacion-e2e.md`)
  - Verificar: `ls docs/specs/group-tables-by-domain/` retorna "no such file"

## Sin cambios

- `docs/diagrams/db-er.mmd` — ya esta actualizado al estado post-rename (refleja el target). Permanente.
- Stack frontend Astro (`apps/*`, `packages/*`) — el rename no expone API publica todavia; `/cv` endpoint planificado consumira nombres nuevos cuando se construya.
- `docker/env/server/.{dev,stage,prod}` — el `DB_URL` apunta al mismo Neon project; no cambia.
- `manifest.yaml` de cada lambda — no cambia (siguen leyendo los mismos SSM params).
- `serverless/migrations/_archive/` — el runner SQL archivado. Permanece como referencia historica.

## Inventario rapido

- **Crear**: 18 archivos de modelos + 1 migracion Alembic + 1 helper + 15 tests = **35 archivos nuevos**
- **Modificar**: 1 schema_extras + 1 seed_service + 2 repositorios + ~10 archivos de los 4 lambdas + ~30 tests existentes = **~44 archivos modificados**
- **Eliminar**: 11 archivos de modelos viejos + 1 carpeta del plan = **12 paths eliminados**

Total: ~91 archivos tocados. Es el commit-set mas grande del repo en 2026.
