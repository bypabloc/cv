# 01 — Contexto, Solución y Criterios de Aceptación

[← README](README.md) · [Fase 1 →](02-fase-stats-summary.md)

## 1. Contexto / Problema

Una auditoría de consistencia cruzó 4 fuentes de la data del CV del
portfolio: schemas Zod + YAML (`packages/content/`), modelos SQLAlchemy,
la migración Alembic y el seed (`db/cv/seed/`). Detectó 3 discrepancias
CRÍTICAS y varias menores.

### Hallazgos de exploración

- **`profile.ts` tiene `stats` inventados a mano que contradicen la
  data**: `companies = 8` (la data real tiene 5 nombres de empresa
  distintos) y `summary` que dice "más de 8 años" cuando `stats` declara
  `yearsExperience = 12`. El usuario confirmó: 12 años es correcto, el
  `summary` quedó desactualizado.
- **`profile.niches` no se persiste**: es campo Zod obligatorio
  (`.min(1)`) pero no existe tabla `profile_niches` y `_seed_profile`
  nunca lo lee. La app lo muestra, la DB no lo guarda.
- **`build-stats.ts` ya tiene la lógica derivada** (`calcYearsExperience`,
  `countCompanies`, `DEFAULT_COUNTRIES = 4`) pero `buildStats()` hace
  short-circuit: si `profile.stats` existe usa esos valores y nunca
  calcula. El docstring del ejemplo ya dice `companies: 5`.
- **`CvSections.astro` recorta `responsibilities[locale].slice(0, 3)`
  para TODAS las apps** (línea 255) — no diferencia generic de niche. Y
  **nunca renderiza `achievements`**: ese campo de cada experiencia
  (logros con métricas) es data existente sin consumir.

## 2. Solución Propuesta

Tres fases de corrección + una de verificación.

1. **Fase 1 — stats + summary**: corregir `profile.ts` (`companies: 5`,
   `yearsExperience: 12` se mantiene, `countries: 4` con comentario) y
   actualizar el `summary` (es + en) de "8 años" a "12 años". Tests de
   `build-stats.ts` que fijan los valores esperados.
2. **Fase 2 — profile_niches en DB**: modelo `ProfileNiche` + tabla
   `profile_niches` + migración Alembic NUEVA encadenada + `_seed_profile`
   que puebla la junction.
3. **Fase 3 — CV genérico enriquecido**: `CvSections` muestra
   `responsibilities` completas + una sección de `achievements` cuando
   `niche === 'generic'`; los niches mantienen el subset (slice 3).
4. **Fase 4 — verificación E2E**: batería completa + refactor de tests +
   limpieza de la carpeta del plan.

### Decisiones clave

- **Decisión 1**: `profile.niches` se persiste en tabla nueva — el
  usuario quiere la DB como fuente de verdad completa. La alternativa
  (quitar la obligatoriedad en Zod) se descartó.
- **Decisión 2**: la migración 81c2cc51db34 NO se edita (ya aplicada en
  prod). Se crea una migración nueva con `down_revision = '81c2cc51db34'`.
- **Decisión 3**: el enriquecimiento de la Fase 3 solo REORGANIZA lo que
  ya existe (deja de recortar, muestra `achievements`). NO escribe
  contenido de CV nuevo — eso requiere input del usuario y va a un plan
  aparte. El cuestionario de feedback se entrega por separado.
- **Decisión 4**: el corte detallado vs subset se decide por
  `niche === 'generic'`. Generic = CV completo; los 4 niches = subset.

## 3. Criterios de Aceptación (AC)

Formato BDD (Given/When/Then).

- **AC-1**: Given `profile.ts`, When se inspecciona `stats.companies`,
  Then vale `5` (cantidad de nombres de empresa distintos en
  `experiences/`).
- **AC-2**: Given `profile.ts`, When se inspecciona `stats.yearsExperience`,
  Then vale `12` y el `summary` (es + en) menciona "12 años" / "12 years",
  NO "8 años" / "8 years".
- **AC-3**: Given `countCompanies(experiences)`, When se ejecuta sobre la
  data real, Then retorna `5`.
- **AC-4**: Given `buildStats()` con `profile.stats` presente, When se
  invoca, Then retorna exactamente `{ yearsExperience: 12, companies: 5,
  countries: 4, certifications: 11 }`.
- **AC-5**: Given el schema PostgreSQL, When se aplica la migración nueva,
  Then existe la tabla `profile_niches` con columnas `(profile_id,
  niche_id)` y PK compuesta.
- **AC-6**: Given la migración nueva, When se ejecuta `downgrade`, Then la
  tabla `profile_niches` se elimina y el schema queda idéntico al estado
  posterior a 81c2cc51db34.
- **AC-7**: Given el seed `_seed_profile`, When corre sobre `profile.ts`,
  Then inserta en `profile_niches` una fila por cada niche de
  `profile.niches` (5 filas: fintech, architect, leader, vibe, generic).
- **AC-8**: Given el modelo `ProfileNiche`, When se compara contra la
  migración nueva, Then las columnas/tipos/nullable coinciden.
- **AC-9**: Given el CV genérico (`apps/generic`), When se renderiza la
  sección de experiencia, Then cada experiencia muestra TODAS sus
  `responsibilities` (sin recorte) y sus `achievements`.
- **AC-10**: Given un CV de nicho (architect/fintech/leader/vibe), When se
  renderiza la experiencia, Then cada experiencia muestra el subset
  (máximo 3 `responsibilities`, sin sección de `achievements`).
- **AC-11**: Given las 6 apps, When se ejecuta `pnpm run build`, Then las
  6 compilan sin error y los stats renderizan `12 / 5 / 4 / 11`.

## 4. Diagrama de Flujo

N/A — el cambio no altera flujos de control. La Fase 3 cambia qué se
renderiza, no la secuencia de pasos.

## 5. Diagrama ER

Aplica: la Fase 2 agrega una tabla. ASCII inline:

```text
                    profile (existente)
                       │ id (uuid, PK)
                       │
        ┌──────────────┴───────────────┐
        │                              │
   profile_stats (existente)     profile_niches (NUEVO)
     profile_id ──> profile.id     profile_id ──> profile.id
     years_experience: int         niche_id   ──> niches.id
     companies: int                PK compuesta (profile_id, niche_id)
     countries: int
     certifications: int        niches (existente)
                                  id (uuid, PK)
                                  slug: string
                                  position: int
```

`profile_niches` replica el patrón de las otras 9 junction `*_niches`
(`experience_niches`, `project_niches`, etc.): unión pura con PK
compuesta, FK con `ondelete='CASCADE'`.

## 6. Tests Requeridos

### 6.A. TDD Flows (Fase 1 — lógica en `build-stats.ts`)

- `WHEN countCompanies(experiences) THEN retorna 5 [AC-3]`
- `WHEN buildStats() con profile.stats presente THEN retorna { yearsExperience: 12, companies: 5, countries: 4, certifications: 11 } [AC-4]`

### 6.B. Unit Tests (Vitest)

- `tests/unit/lib/build-stats.test.ts` (en `packages/app-shared/`):
  cubre `countCompanies`, `calcYearsExperience`, `buildStats` [AC-3, AC-4].
  Si ya existe, se extiende; si no, se crea (path mirroring).
- Fase 3: test del componente `CvSections` o de un helper extraído que
  decida el corte detallado/subset [AC-9, AC-10].
- Coverage v8 >= 80% per-file en archivos modificados.

### 6.C. Typecheck

- `pnpm exec tsc --noEmit` + `pnpm exec astro check`.

### 6.D. E2E Tests (Playwright)

Aplica: la Fase 3 cambia el render visible. La verificación E2E de la
Fase 4 corre la suite Playwright contra el stack local (los 6
subdominios) — ver `07-verificacion-e2e.md`. NO se agregan specs nuevas:
la suite existente valida que las 6 apps renderizan sin 502 y los stats
se ven; basta para AC-11.

## 7. Archivos Afectados

### Crear

- `serverless/lambda/shared/db/alembic/versions/<rev>_add_profile_niches.py`
  — migración Alembic nueva (`down_revision = '81c2cc51db34'`).
  - Verificar: `upgrade` + `downgrade` + `upgrade` en branch Neon de prueba.
- `packages/app-shared/tests/unit/lib/build-stats.test.ts` — si no existe.
  - Verificar: `pnpm --filter @portfolio/app-shared exec vitest run`.

### Modificar

- `packages/content/src/data/profile.ts` — `stats.companies: 5`, comentario
  en `countries`, `summary` es/en de "8 años" a "12 años".
  - Verificar: `pnpm --filter @portfolio/content exec vitest run`.
- `serverless/lambda/shared/db/models/profile.py` — agregar clase
  `ProfileNiche`.
  - Verificar: `python -m compileall serverless/lambda/shared/db/models`.
- `serverless/lambda/shared/db/models/__init__.py` — exportar `ProfileNiche`,
  actualizar conteo en docstring.
  - Verificar: `python -c "from db.models import ProfileNiche"`.
- `serverless/lambda/shared/db/base.py` — corregir conteo de tablas en
  docstring (35 → 36).
  - Verificar: lectura.
- `db/cv/seed/seed_from_yaml.py` — `_seed_profile` puebla `profile_niches`.
  - Verificar: `python -m compileall db/cv/seed`.
- `packages/app-shared/src/components/CvSections.astro` — render detallado
  para `niche === 'generic'` (responsibilities completas + achievements).
  - Verificar: `pnpm --filter @portfolio/app-shared exec astro check` +
    `pnpm run build`.

### Eliminar

- `docs/specs/cv-data-consistency/` — en el último commit (Fase 4).
  - Verificar: `git rm -r docs/specs/cv-data-consistency/`.

[← README](README.md) · [Fase 1 →](02-fase-stats-summary.md)
