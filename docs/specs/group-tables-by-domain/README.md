# Plan — group-tables-by-domain

> Renombra las 37 tablas del schema unificado de Neon agrupandolas por
> dominio con prefijo (`cv_`, `vis_`, `tax_`, `i18n_`), reorganiza los
> modelos SQLAlchemy en subcarpetas, normaliza nombres de columnas y
> tipos de fecha, agrega slugs faltantes y refresca el schema en stage
> y prod desde cero (data vieja descartada por decision del usuario).

## Estado

| Fase | Archivo | Estado |
|---|---|---|
| Contexto, solucion, AC | [01-contexto-y-decision.md](01-contexto-y-decision.md) | escrito |
| Diagrama ER (referencia + renames) | [02-diagrama-er.md](02-diagrama-er.md) | escrito |
| Tests requeridos | [03-tests-requeridos.md](03-tests-requeridos.md) | escrito |
| Archivos afectados | [04-archivos-afectados.md](04-archivos-afectados.md) | escrito |
| Fase 1 — modelos + reorganizacion | [05-fase-modelos-reorganizacion.md](05-fase-modelos-reorganizacion.md) | escrito |
| Fase 2 — migracion Alembic | [06-fase-migracion-alembic.md](06-fase-migracion-alembic.md) | escrito |
| Fase 3 — seeds + seed_service | [07-fase-seeds-update.md](07-fase-seeds-update.md) | escrito |
| Fase 4 — lambdas downstream | [08-fase-lambdas-update.md](08-fase-lambdas-update.md) | escrito |
| Fase 5 — provision stage/prod desde cero | [09-fase-provision-stage-prod.md](09-fase-provision-stage-prod.md) | escrito |
| Commits | [10-commits.md](10-commits.md) | escrito |
| Paralelizacion con worktrees | [11-paralelizacion-worktrees.md](11-paralelizacion-worktrees.md) | escrito |
| Verificacion E2E iterativa | [12-verificacion-e2e.md](12-verificacion-e2e.md) | escrito |
| Mapeo exhaustivo de usos (anexo grep) | [13-mapeo-usos-modelos.md](13-mapeo-usos-modelos.md) | generado (999 lineas, 1000+ ocurrencias por fase) |

## Decisiones no-reabribles (consolidado de 4 rondas de Q&A)

| # | Decision | Valor |
|---|---|---|
| 1 | Mecanismo de agrupacion | Prefijo en `__tablename__` (NO PG schemas) |
| 2 | Grupos | 4 — `cv` / `visitor` / `taxonomy` / `i18n` |
| 3 | Alcance | Renombrar las 37 tablas ahora en UNA migracion Alembic |
| 4 | Prefijo en junctions | Mismo que entidad padre |
| 5 | Prefijos exactos | `cv_` / `vis_` / `tax_` / `i18n_` |
| 6 | Tablas borderline | `event_types` -> `tax_`, `niche_priorities` -> `tax_` |
| 7 | Codigo Python | Reorganizar carpetas + `__tablename__`. Clases conservan nombre. |
| 8 | Declaracion del prefijo | Explicito en `__tablename__` por clase (NO base abstracta) |
| 9 | Pluralizacion | Todo plural |
| 10 | `profile` singular | -> `cv_profiles` (plural forzado) |
| 11 | `education` non-count | -> `cv_education_entries` |
| 12 | `references` reservada SQL | -> `cv_endorsements` |
| 13 | Junction `references` cascade | -> `cv_endorsement_niches` |
| 14 | Junction `education` cascade | -> `cv_education_entry_niches` |
| 15 | Normalizacion de fechas | DATE + naming `*_on` (started_on, ended_on, awarded_on) |
| 16 | Conversion fechas en seeder | `f"{ym}-01"` automatico, YAMLs sin cambio |
| 17 | Slug en `skills` y `tech_tags` | Agregar `slug VARCHAR(120) UK` |
| 18 | `name` en `cv_skills` y `tax_tech_tags` | Directo (NO movido a i18n_translations) |
| 19 | `niches.position` | -> `tax_niches.display_order` |
| 20 | `vis_tracking_events` PK | PK fisica `(created_at, visit_id, page_id)` |
| 21 | Deploy strategy | Atomico (1 PR, migrate -> deploy lambdas en mismo CI run) |
| 22 | stage + prod | Rehacer desde cero (destroy + provision + migrate + seed). Data vieja descartada. |

## Reglas criticas

- SIEMPRE escribir tests ANTES del codigo (TDD obligatorio, ver `tdd-workflow`)
- SIEMPRE verificar antes de declarar listo cada commit (`pytest`, `serverless tests`)
- SIEMPRE preservar la coherencia: clases Python conservan nombre, solo cambia `__tablename__` y path
- NUNCA editar una migracion Alembic ya aplicada en prod (esta es nueva, todavia no aplicada)
- NUNCA atribucion de IA en commits / PRs

## Estado actual del schema (snapshot pre-rename)

- Branch `dev` Neon: 37 tablas + `alembic_version` + `tracking_events_default` (particion). Alembic en `d4e5f6a7b8c9`. Data: 372 translations, 99 skills, 9 experiences, 4 projects.
- Branch `stage` Neon: schema viejo SQL (7 tablas), Alembic NO aplicado. Se descarta.
- Branch `production` Neon: igual a stage. Se descarta.

## Diagrama ER (estado objetivo post-rename)

Archivo: [`docs/diagrams/db-er.mmd`](../../diagrams/db-er.mmd). Refleja el
estado **post-rename** con las 37 tablas prefijadas + columnas normalizadas
+ PK fisica en `vis_tracking_events`. 300 lineas, validado con mermaid
11.15.0 (SVG generado limpio, ~732 KB).

## Como ejecutar el plan

1. Leer `01-contexto-y-decision.md` para entender el por que.
2. Revisar `02-diagrama-er.md` y el `.mmd` para el target schema.
3. Seguir las fases en orden (05 -> 06 -> 07 -> 08 -> 09).
4. Cada commit del plan ejecuta su verificacion incremental ANTES de
   commitear (ver `10-commits.md`).
5. Lanzar worktrees segun `11-paralelizacion-worktrees.md` cuando sea
   safe (despues del commit 4).
6. La ultima fase es la bateria E2E iterativa (`12-verificacion-e2e.md`):
   no se hace `git push` ni se crea PR hasta que toda la suite este
   verde.

## Ciclo de vida

Esta carpeta `docs/specs/group-tables-by-domain/` es **efimera**. El
ultimo commit del PR (el de la seccion 12) la elimina con
`git rm -r docs/specs/group-tables-by-domain/`. La trazabilidad del plan
queda en `git log` y el PR mergeado. El `.mmd` SI permanece en
`docs/diagrams/`.
