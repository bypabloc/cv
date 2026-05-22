# Sección 9 — Commits

[← Fase 3](04-fase-cv-generico.md) · [Paralelización →](06-paralelizacion-worktrees.md)

Commits incrementales en `feature/cv-data-consistency` (desde `dev`). Cada
commit deja el repo verde y ejecuta su verificación ANTES de commitear.

## Secuencia

### Commit 1 — `docs(specs): plan de consistencia de datos del CV`

- Agrega `docs/specs/cv-data-consistency/` (README + 7 docs).
- Verificación: `pnpm exec biome check docs` (markdown lint si aplica) +
  lectura.

### Commit 2 — `fix(content): corrige stats.companies y summary del profile`

- `profile.ts`: `companies: 8 → 5`, comentario en `countries`, `summary`
  es/en de "8 años" a "12 años".
- `build-stats.test.ts`: tests con valores correctos (countCompanies == 5,
  buildStats objeto exacto).
- Cubre AC-1, AC-2, AC-3, AC-4.
- Verificación incremental:
  ```bash
  pnpm --filter @portfolio/content exec vitest run
  pnpm --filter @portfolio/app-shared exec vitest run
  pnpm --filter @portfolio/content run typecheck
  ```

### Commit 3 — `feat(db): agrega tabla profile_niches al schema del CV`

- Modelo `ProfileNiche` en `models/profile.py`.
- `models/__init__.py`: export + conteo 36.
- `base.py`: docstring corregido a 36.
- Migración Alembic nueva (`<rev>_add_profile_niches.py`,
  `down_revision = '81c2cc51db34'`).
- Cubre AC-5, AC-6, AC-8.
- Verificación incremental:
  ```bash
  python -m compileall -q serverless/lambda/shared/db
  cd serverless/lambda && .venv/bin/python -c \
    "from shared.db.models import ProfileNiche"
  # migración: upgrade+downgrade+upgrade en branch Neon de prueba
  #   (o alembic upgrade/downgrade --sql si no hay Neon)
  ```

### Commit 4 — `feat(db): el seed puebla profile_niches`

- `seed_from_yaml.py`: `_seed_profile` recibe `niche_ids` y llama a
  `_link_niches` para `profile_niches`; `run_seed` pasa el parámetro.
- Cubre AC-7.
- Verificación incremental:
  ```bash
  python -m compileall -q db/cv/seed
  # si hay Neon: seed en branch de prueba + verificar 5 filas
  ```

### Commit 5 — `feat(app-shared): el CV genérico muestra el detalle completo`

- `cv-detail.ts` nuevo (`isDetailedCv`, `visibleResponsibilities`,
  `NICHE_RESPONSIBILITIES_LIMIT`).
- `cv-detail.test.ts` nuevo (4 casos).
- `CvSections.astro`: usa el helper; render detallado para `generic`
  (responsibilities completas + achievements), subset para los niches.
- `elements.{es,en}.yaml`: label `achievements` si no existía (+ schema
  si `labels` es objeto cerrado).
- Cubre AC-9, AC-10.
- Verificación incremental:
  ```bash
  pnpm --filter @portfolio/app-shared exec vitest run
  pnpm --filter @portfolio/content exec vitest run
  pnpm --filter @portfolio/app-shared run typecheck
  pnpm exec biome check packages/app-shared packages/content
  pnpm run build
  ```

### Commit 6 — `test(cv-data): verificación E2E del plan de consistencia`

- Es la Fase 4 (sección 11). Ejecuta la batería completa de verificación.
- Incluye `git rm -r docs/specs/cv-data-consistency/` (la carpeta del plan
  es efímera).
- Cubre AC-11.
- Verificación: ver `07-verificacion-e2e.md` — batería completa.

## Resumen de la secuencia

| Commit | Tipo | Deja verde | AC |
|--------|------|------------|-----|
| 1 | docs | sí (solo docs) | — |
| 2 | fix(content) | sí | AC-1..4 |
| 3 | feat(db) | sí | AC-5,6,8 |
| 4 | feat(db) | sí | AC-7 |
| 5 | feat(app-shared) | sí | AC-9,10 |
| 6 | test | sí | AC-11 |

## PR

Un solo PR `feature/cv-data-consistency -> dev`, merge commit. El body
sigue el template del proyecto (Problema / Solución / Cómo probar / TODO).
El "Cómo probar" reutiliza la batería de la sección 11.

[← Fase 3](04-fase-cv-generico.md) · [Paralelización →](06-paralelizacion-worktrees.md)
