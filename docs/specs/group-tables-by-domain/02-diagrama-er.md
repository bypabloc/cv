# 02 — Diagrama ER (referencia + renames)

[README](README.md) | [01-contexto](01-contexto-y-decision.md) |
**02-diagrama-er** | [03-tests](03-tests-requeridos.md)

## Diagrama ER del estado objetivo

Archivo permanente: [`docs/diagrams/db-er.mmd`](../../diagrams/db-er.mmd)

El `.mmd` refleja el **estado post-rename** con todas las tablas
prefijadas, columnas normalizadas, slugs agregados y PK fisica en
`vis_tracking_events`. Validado con mermaid 11.15.0 (SVG generado
limpio).

## Tabla de renames (37 tablas)

### CV (28 tablas)

| Hoy | Despues | Cambio adicional |
|---|---|---|
| `profile` | `cv_profiles` | singular -> plural forzado |
| `profile_stats` | `cv_profile_stats` | solo prefijo |
| `profile_niches` | `cv_profile_niches` | solo prefijo |
| `experiences` | `cv_experiences` | `start_ym/end_ym VARCHAR(7)` -> `started_on/ended_on DATE` |
| `experience_bullets` | `cv_experience_bullets` | solo prefijo |
| `experience_niches` | `cv_experience_niches` | solo prefijo |
| `experience_skills` | `cv_experience_skills` | solo prefijo |
| `education` | `cv_education_entries` | rename entidad (non-count noun) |
| `education_niches` | `cv_education_entry_niches` | cascade del rename anterior; FK `education_entry_id` |
| `projects` | `cv_projects` | solo prefijo |
| `project_case_studies` | `cv_project_case_studies` | solo prefijo |
| `project_metrics` | `cv_project_metrics` | solo prefijo |
| `project_niches` | `cv_project_niches` | solo prefijo |
| `project_tech_tags` | `cv_project_tech_tags` | solo prefijo |
| `skills` | `cv_skills` | + `slug VARCHAR(120) UK` |
| `skill_categories` | `cv_skill_categories` | solo prefijo |
| `skill_category_skills` | `cv_skill_category_skills` | solo prefijo |
| `skill_category_niches` | `cv_skill_category_niches` | solo prefijo |
| `awards` | `cv_awards` | `awarded_ym VARCHAR(7)` -> `awarded_on DATE` |
| `award_niches` | `cv_award_niches` | solo prefijo |
| `certificates` | `cv_certificates` | solo prefijo (issued_on ya era DATE) |
| `certificate_niches` | `cv_certificate_niches` | solo prefijo |
| `languages` | `cv_languages` | solo prefijo |
| `language_niches` | `cv_language_niches` | solo prefijo |
| `publications` | `cv_publications` | solo prefijo (published_on ya era DATE) |
| `publication_niches` | `cv_publication_niches` | solo prefijo |
| `references` | **`cv_endorsements`** | rename (palabra reservada SQL) |
| `reference_niches` | **`cv_endorsement_niches`** | cascade; FK `endorsement_id` |

### Visitor (4 tablas)

| Hoy | Despues | Cambio adicional |
|---|---|---|
| `contacts` | `vis_contacts` | solo prefijo |
| `sessions` | `vis_sessions` | solo prefijo |
| `session_visits` | `vis_session_visits` | solo prefijo |
| `tracking_events` | `vis_tracking_events` | + PK fisica `(created_at, visit_id, page_id)` |

### Taxonomy (4 tablas)

| Hoy | Despues | Cambio adicional |
|---|---|---|
| `niches` | `tax_niches` | `position INT` -> `display_order INT` |
| `niche_priorities` | `tax_niche_priorities` | solo prefijo |
| `tech_tags` | `tax_tech_tags` | + `slug VARCHAR(120) UK` |
| `event_types` | `tax_event_types` | solo prefijo |

### i18n (1 tabla)

| Hoy | Despues | Cambio adicional |
|---|---|---|
| `translations` | `i18n_translations` | solo prefijo |

## ENUMs (sin rename pero con cambio de valor)

| ENUM | Cambio |
|---|---|
| `entity_type` | `ALTER TYPE entity_type RENAME VALUE 'reference' TO 'endorsement'` |
| `seniority`, `bullet_kind`, `skill_kind`, `project_status`, `project_type`, `locale` | Sin cambios |

## FKs renombradas (cascade del rename de tabla padre)

| Tabla | FK column antes | FK column despues |
|---|---|---|
| `cv_education_entry_niches` | `education_id` | `education_entry_id` |
| `cv_endorsement_niches` | `reference_id` | `endorsement_id` |

El resto de FKs preservan el nombre de columna (`profile_id`,
`experience_id`, `project_id`, `niche_id`, etc.) — solo cambia el
nombre de la TABLA referenciada en el constraint.

## Constraints regenerados (Alembic naming convention)

La migracion regenera nombres de constraints siguiendo la convencion
Alembic configurada en `env.py`:

- PK: `pk_<table_name>`
- FK: `fk_<table_name>_<col>_<ref_table>`
- UK: `uq_<table_name>_<col>`
- Index: `ix_<table_name>_<col>`
- CHECK: `ck_<table_name>_<short_name>`

Ejemplo: `pk_profile` -> `pk_cv_profiles`, `fk_education_niches_education_id_education`
-> `fk_cv_education_entry_niches_education_entry_id_cv_education_entries`.

## Tipos PG (sin cambios)

`citext` (en `vis_contacts.email`), `inet` (`vis_session_visits.ip`),
`char(2)` (`vis_session_visits.country`), `jsonb` (`vis_tracking_events.event_props`,
`vis_session_visits.utm_*` no aplica — son `text`), `timestamptz`,
`uuid` siguen como hoy.

## Trigger polimorfico

`assert_entity_exists(entity_type, entity_id)` requiere actualizar la
lookup table interna del trigger:

| Antes | Despues |
|---|---|
| `'profile' -> profile` | `'profile' -> cv_profiles` |
| `'experience' -> experiences` | `'experience' -> cv_experiences` |
| `'experience_bullet' -> experience_bullets` | `'experience_bullet' -> cv_experience_bullets` |
| `'project' -> projects` | `'project' -> cv_projects` |
| `'project_case_study' -> project_case_studies` | `'project_case_study' -> cv_project_case_studies` |
| `'education' -> education` | `'education' -> cv_education_entries` |
| `'award' -> awards` | `'award' -> cv_awards` |
| `'certificate' -> certificates` | `'certificate' -> cv_certificates` |
| `'language' -> languages` | `'language' -> cv_languages` |
| `'publication' -> publications` | `'publication' -> cv_publications` |
| `'reference' -> references` | `'endorsement' -> cv_endorsements` |
| `'skill_category' -> skill_categories` | `'skill_category' -> cv_skill_categories` |

Los valores del enum siguen siendo strings cortos (`'profile'`,
`'experience'`, etc.); solo el rename de `'reference' -> 'endorsement'`
afecta semantica.

## Particion de `vis_tracking_events`

Particion `tracking_events_default` se renombra a
`vis_tracking_events_default`. El `CREATE TABLE ... PARTITION OF
vis_tracking_events DEFAULT` se regenera. La nueva PK fisica
`(created_at, visit_id, page_id)` se aplica a la tabla padre y se
hereda por las particiones.

## Diagrama de flujo de datos (sin cambios estructurales)

```text
Browser
   |
   v (POST /track o /contact)
API Gateway -- Lambda contact_form / tracking_pixel -- DynamoDB
                                                          |
                                                          v (DDB Stream)
                                              Lambda stream_processor
                                                          |
                                                          v (psycopg3)
                                                       Neon PG
                                                       (vis_*, cv_*)
```

El flujo es identico al actual; solo cambian los nombres de las tablas
de destino.
