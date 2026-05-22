# Sección 9 — Commits

[← Fase 6](07-fase-paginas-detalle.md) · [Paralelización →](09-paralelizacion-worktrees.md)

Commits en `feature/cv-content-enrichment` (desde `dev`). Cada commit
deja el repo verde y ejecuta su verificación ANTES de commitear.

## Secuencia

### Commit 1 — `docs(specs): plan de enriquecimiento de contenido del CV`

- Agrega `docs/specs/b-cv-content-enrichment/` (README + 10 docs + anexo).
- Verificación: lectura.

### Commit 2 — `feat(content): agrega country y metricsEstimated al schema`

- `schemas.ts`: `country` en `ExperienceSchema`, `metricsEstimated` en
  `ExperienceSchema` y `ProjectSchema`.
- Las 9 experiencias YAML reciben `country` (solo el campo, sin tocar el
  resto del contenido aún).
- `data-parity` baseline de experiences actualizado.
- Cubre AC-1, AC-2 (parcial).
- Verificación: `vitest` content + typecheck.

### Commit 3 — `feat(db): propaga country y metrics_estimated a PostgreSQL`

- Modelos `Experience` (+`country`, +`metrics_estimated`) y `Project`
  (+`metrics_estimated`).
- Migración Alembic nueva encadenada a `79bacfd3c091`.
- `seed_from_yaml.py`: `_seed_experiences` y `_seed_projects` insertan
  los campos.
- Cubre AC-3b, AC-3c, AC-3d.
- Verificación: `compileall` + el modelo importa + tests `shared` +
  migración `upgrade`/`downgrade` (`--sql` o branch Neon).

### Commit 4 — `feat(content): reestructura experiencias y reorienta por nicho`

- Las 4 "Independiente / Académico" reciben su `company` real.
- `achievements`/`responsibilities` reorientados por nicho, con métricas.
- `metricsEstimated: true` donde aplique.
- `data-parity` baseline de experiences actualizado.
- Anexo `11-metricas-estimadas.md` actualizado (sección experiencias).
- Cubre AC-4, AC-5, AC-7 (experiencias).
- Verificación: `vitest` content + typecheck.

### Commit 5 — `feat(content): completa case studies y agrega el proyecto cv`

- `caseStudyDetailed` + `metrics` en los 6 proyectos.
- Proyecto `cv.yaml` nuevo.
- `metricsEstimated` donde aplique; anexo actualizado (sección proyectos).
- `data-parity` baseline de projects actualizado.
- Cubre AC-6, AC-7 (proyectos), AC-8.
- Verificación: `vitest` content + typecheck.

### Commit 6 — `feat(content): summary por nicho en el i18n curriculum`

- `hero.summary` específico en los 5 `curriculum/<nicho>.{es,en}.yaml`.
- Test del merge del summary por nicho.
- Cubre AC-9, AC-10.
- Verificación: `vitest` content + app-shared + typecheck.

### Commit 7 — `feat(app-shared): componentes de detalle de experiencia y proyecto`

- `ExperienceDetail.astro` y `ProjectDetail.astro` en `app-shared`.
- Si hace falta, prop `href`/modo compacto en `TimelineItem` /
  `ProjectBentoCard`.
- Verificación: `astro check` + `biome` + `vitest` app-shared.

### Commit 8 — `feat(apps): paginas de detalle /experience y /projects`

- Las 24 rutas dinámicas thin wrapper en las 6 apps.
- `CvSections.astro`: enlaces desde las tarjetas + tarjeta resumen para
  experiencias antiguas no-relevantes al nicho.
- Cubre AC-11, AC-12, AC-13.
- Verificación: `pnpm run build` (las ~192 páginas) + `biome` +
  typecheck.

### Commit 9 — `test(cv-content): verificacion E2E del plan de enriquecimiento`

- Fase 7 (sección 11): batería completa.
- Anexo `11-metricas-estimadas.md` final, completo.
- Incluye `git rm -r docs/specs/b-cv-content-enrichment/`.
- Cubre AC-14.
- Verificación: ver `10-verificacion-e2e.md` — batería completa.

## Resumen de la secuencia

| Commit | Tipo | Fase | AC |
|--------|------|------|-----|
| 1 | docs | — | — |
| 2 | feat(content) | 1 | AC-1, AC-2 |
| 3 | feat(db) | 2 | AC-3b, AC-3c, AC-3d |
| 4 | feat(content) | 3 | AC-4, AC-5, AC-7 |
| 5 | feat(content) | 4 | AC-6, AC-7, AC-8 |
| 6 | feat(content) | 5 | AC-9, AC-10 |
| 7 | feat(app-shared) | 6 | — (preparación) |
| 8 | feat(apps) | 6 | AC-11, AC-12, AC-13 |
| 9 | test | 7 | AC-14 |

## PR

Un solo PR `feature/cv-content-enrichment -> dev`, merge commit. El body
sigue el template del proyecto. El "Cómo probar" reutiliza la batería de
la sección 11. **El PR debe destacar en el cuerpo** que el plan introdujo
cifras estimadas (`metricsEstimated: true`) y enlazar al anexo
`11-metricas-estimadas.md` para que el reviewer (el propio usuario) las
valide antes del merge a `stage`/`main`.

[← Fase 6](07-fase-paginas-detalle.md) · [Paralelización →](09-paralelizacion-worktrees.md)
