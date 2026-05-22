# 01 — Contexto, Solución y Criterios de Aceptación

[← README](README.md) · [Fase 1 →](02-fase-schema-zod.md)

## 1. Contexto / Problema

El plan A (`cv-data-consistency`) corrigió 3 discrepancias de datos
rotos. Quedó pendiente el **enriquecimiento de contenido**: el CV hoy es
correcto pero poco diferenciado por nicho y con experiencias antiguas sin
contexto.

### Hallazgos de exploración

- **No hay rutas dinámicas** en ninguna app. Las 6 apps tienen solo
  `index`, `about`, `certificates`, `contact`. Para páginas de detalle
  hay que crear `[slug].astro` + `getStaticPaths()`.
- **El proyecto NO usa content collections de Astro**. La data viene de
  `@portfolio/content` (`import { experiences, projects }`).
  `getStaticPaths()` debe usar ese import, NO `getCollection()`.
- **4 experiencias agrupadas como "Independiente / Académico"**
  (`corpoelec`, `ipasme`, `iai`, `projects-degrees`, 2013-2015) sin
  contexto real ni país.
- **`ExperienceSchema` no tiene `country`**; `stats.countries` es manual.
- **`CurriculumStringsSchema.hero` ya tiene `summary`**: el summary por
  nicho se logra con el merge `_base` + `<nicho>` que ya existe.
- **2 proyectos sin `caseStudyDetailed`** (`mvp-template-full-stack`,
  `portfolio-astro`); 1 sin `metrics` (`portfolio-astro`).
- El patrón de páginas: thin wrapper por app + componente compartido en
  `packages/app-shared/`.

## 2. Solución Propuesta

Siete fases.

1. **Fase 1 — schema Zod**: agregar `country` a `ExperienceSchema` y
   `metricsEstimated` (interno) a `ExperienceSchema` y `ProjectSchema`,
   en `packages/content/`. Agregar `country` a las 9 experiencias para
   que el commit deje el repo verde.
2. **Fase 2 — DB (migración Alembic)**: propagar los campos nuevos a la
   base PostgreSQL — migración Alembic nueva (`experiences.country`,
   `experiences.metrics_estimated`, `projects.metrics_estimated`),
   modelos SQLAlchemy y el seed. NO se tocan los `_archive/*.sql`.
3. **Fase 3 — experiencias**: reestructurar las 4 "Independiente /
   Académico" con contexto real; reorientar el contenido por nicho;
   generar logros con métricas.
4. **Fase 4 — proyectos**: completar `caseStudyDetailed` + `metrics` en
   los 6 proyectos; agregar el proyecto `cv`.
5. **Fase 5 — summary por nicho**: agregar `hero.summary` específico en
   cada `curriculum/<nicho>.{es,en}.yaml`.
6. **Fase 6 — páginas de detalle**: componentes `ExperienceDetail` y
   `ProjectDetail` en `app-shared`; rutas `[slug].astro` (es + en) para
   experience y projects en las 6 apps; enlaces desde las tarjetas.
7. **Fase 7 — verificación E2E**: batería completa + anexo de métricas +
   limpieza.

> El orden importa: Fase 1 (schema Zod) y Fase 2 (DB) van primero porque
> la data de las fases 3-4 depende de que los campos existan. La Fase 2
> es independiente del frontend (backend Python) y podría ir en paralelo
> a las fases 3-5 — ver `09-paralelizacion-worktrees.md`.

### Decisiones clave

Ver la tabla "Decisiones no reabribles" del [README](README.md) (D-1 a
D-15). Las más estructurales:

- **Decisión métricas (D-2)**: las cifras inventadas son plausibles y
  conservadoras. Cada entry con cifras estimadas lleva
  `metricsEstimated: true` — campo del YAML que el render IGNORA, solo
  sirve para que el usuario sepa qué revisar. El anexo
  `11-metricas-estimadas.md` lista cada cifra con su justificación.
- **Decisión páginas de detalle (D-6)**: `getStaticPaths()` con el
  import de `@portfolio/content`. ~180 páginas estáticas nuevas (15
  slugs × 2 locales × 6 apps). Las 6 apps comparten los componentes
  `ExperienceDetail`/`ProjectDetail` de `app-shared`.
- **Decisión idioma (D-13, D-14)**: inglés con tono US (no literal);
  todo texto en español neutro, sin modismos regionales.

## 3. Criterios de Aceptación (AC)

Formato BDD (Given/When/Then).

- **AC-1**: Given `ExperienceSchema`, When se valida una experiencia con
  `country`, Then el campo se acepta como string.
- **AC-2**: Given las 9 experiencias YAML, When se cargan, Then cada una
  declara `country` con un país real (Venezuela, Perú, Chile o México).
- **AC-3**: Given `stats.countries` en `profile.ts`, When se compara con
  los `country` distintos de las experiencias, Then coinciden (4).
- **AC-3b**: Given el modelo SQLAlchemy `Experience`, When se aplica la
  migración Alembic de la Fase 2, Then la tabla `experiences` tiene
  columna `country` (NOT NULL) y `metrics_estimated` (Boolean), y
  `projects` tiene `metrics_estimated`.
- **AC-3c**: Given la migración Alembic de la Fase 2, When se ejecuta
  `downgrade`, Then las 3 columnas se eliminan y el schema queda como
  tras la migración anterior.
- **AC-3d**: Given el seed `seed_from_yaml.py`, When corre, Then inserta
  el `country` de cada experiencia y el flag `metrics_estimated` de
  experiencias y proyectos en sus columnas.
- **AC-4**: Given las 4 experiencias antes agrupadas, When se inspeccionan,
  Then cada una tiene un `company` con su institución real (no todas
  "Independiente / Académico").
- **AC-5**: Given un CV de nicho, When se lee una experiencia relevante a
  ese nicho, Then sus `responsibilities`/`achievements` enfatizan el
  ángulo del nicho.
- **AC-6**: Given los 6 proyectos + el proyecto `cv`, When se cargan,
  Then los 7 tienen `caseStudyDetailed` y `metrics` no vacíos.
- **AC-7**: Given una entry con cifras estimadas, When se inspecciona el
  YAML, Then tiene `metricsEstimated: true`, y ese campo NO aparece en el
  HTML renderizado.
- **AC-8**: Given el proyecto `cv`, When se carga, Then existe con su
  `repo` apuntando a `https://github.com/bypabloc/cv`.
- **AC-9**: Given `curriculum/<nicho>.es.yaml` para los 5 niches, When se
  invoca `getCurriculum(<nicho>, 'es')`, Then `hero.summary` es el texto
  específico del nicho (no el del `_base`).
- **AC-10**: Given un nicho sin `hero.summary` propio, When se invoca
  `getCurriculum`, Then `hero.summary` cae al `_base` (merge shallow).
- **AC-11**: Given las 6 apps, When se ejecuta `pnpm run build`, Then se
  genera una página `/experience/<slug>` por cada una de las 9
  experiencias, en es y en en.
- **AC-12**: Given las 6 apps, When se ejecuta `pnpm run build`, Then se
  genera una página `/projects/<slug>` por cada uno de los 7 proyectos,
  en es y en en.
- **AC-13**: Given la tarjeta de una experiencia/proyecto en el home,
  When se renderiza, Then incluye un enlace a su página de detalle.
- **AC-14**: Given cualquier texto nuevo del CV, When se revisa, Then
  está en español neutro (sin modismos regionales) y el inglés tiene
  tono US.

## 4. Diagrama de Flujo

Aplica: la Fase 5 agrega rutas. ASCII inline del routing nuevo:

```text
ANTES (cada app)                  DESPUES (cada app)
  /                                 /
  /about                            /about
  /certificates                     /certificates
  /contact                          /contact
  /en/...                           /experience/<slug>      (NUEVO, x9)
                                    /projects/<slug>        (NUEVO, x7)
                                    /en/...
                                    /en/experience/<slug>   (NUEVO, x9)
                                    /en/projects/<slug>     (NUEVO, x7)
```

## 5. Diagrama ER

Aplica: cambios en las content collections (schemas Zod). ASCII inline,
`(*)` campo nuevo:

```text
ExperienceSchema                    ProjectSchema
  slug: string                        slug: string
  role: BiLang                        name: string
  company: string                     summary: BiLang
  country: string (*)                 ...
  companyUrl?: string                 caseStudyDetailed: object
  start: YYYY-MM                         (sin cambio de schema,
  end?: YYYY-MM                           pasa a estar en los 6)
  niches: Niche[]                      metrics: record (idem)
  ...                                  metricsEstimated: boolean (*)
  metricsEstimated: boolean (*)        projectType: enum

CurriculumStringsSchema.hero
  summary: string  (ya existe — se usa el override por nicho)
```

## 6. Tests Requeridos

### 6.A. TDD Flows

- `WHEN ExperienceSchema.parse con country THEN acepta el campo [AC-1]`
- `WHEN getCurriculum('fintech','es') THEN hero.summary es el de fintech [AC-9]`
- `WHEN getCurriculum de un nicho sin summary propio THEN hero.summary cae al _base [AC-10]`

### 6.B. Unit Tests (Vitest)

- `packages/content/tests/unit/` — los schemas (`country`,
  `metricsEstimated`); paridad de slugs de las 9 experiencias + 7
  proyectos; el `data-parity` baseline se actualiza (cambio deliberado).
- `packages/app-shared/tests/unit/` — helper de `getStaticPaths` si se
  extrae uno; merge del summary por nicho.
- Coverage >= 80% per-file en archivos modificados.

### 6.C. Typecheck

- `pnpm exec tsc --noEmit` + `pnpm exec astro check` (las rutas
  `[slug].astro` nuevas).

### 6.D. E2E Tests (Playwright)

Aplica: la Fase 5 agrega páginas navegables. La verificación E2E de la
Fase 6 corre la suite Playwright. Se evalúa agregar specs que naveguen a
una página de detalle de experiencia y una de proyecto y verifiquen que
renderizan (no 404). Decisión final en `09-verificacion-e2e.md`.

## 7. Archivos Afectados

### Crear

- `packages/app-shared/src/components/ExperienceDetail.astro` — vista de
  detalle de una experiencia.
  - Verificar: `pnpm --filter @portfolio/app-shared exec astro check`.
- `packages/app-shared/src/components/ProjectDetail.astro` — vista de
  detalle de un proyecto.
  - Verificar: idem.
- `apps/<app>/src/pages/experience/[slug].astro` (×6) +
  `apps/<app>/src/pages/en/experience/[slug].astro` (×6).
  - Verificar: `pnpm run build` genera las páginas.
- `apps/<app>/src/pages/projects/[slug].astro` (×6) +
  `apps/<app>/src/pages/en/projects/[slug].astro` (×6).
  - Verificar: idem.
- `packages/content/src/data/projects/cv.yaml` — proyecto nuevo.
  - Verificar: `pnpm --filter @portfolio/content exec vitest run`.
- `packages/content/src/data/experiences/<nuevos-slugs>.yaml` — al
  separar las 4 "Independiente / Académico" (si cambian de slug).
  - Verificar: idem.
- `serverless/lambda/shared/db/alembic/versions/<rev>_add_cv_country_metrics.py`
  — migración Alembic nueva (Fase 2).
  - Verificar: `upgrade`/`downgrade` (`--sql` o branch Neon).
- `docs/specs/b-cv-content-enrichment/11-metricas-estimadas.md` — anexo.

### Modificar (backend — Fase 2)

- `serverless/lambda/shared/db/models/experience.py` — columnas `country`
  + `metrics_estimated` en el modelo `Experience`.
  - Verificar: `compileall` + el modelo importa.
- `serverless/lambda/shared/db/models/project.py` — columna
  `metrics_estimated` en el modelo `Project`.
  - Verificar: idem.
- `db/cv/seed/seed_from_yaml.py` — `_seed_experiences` y `_seed_projects`
  insertan los campos nuevos.
  - Verificar: `compileall` + tests del seed.
- `serverless/migrations/_archive/*.sql` — **NO se tocan** (archivados,
  no se aplican; ver D-15).

### Modificar

- `packages/content/src/schemas.ts` — `country` + `metricsEstimated`.
- `packages/content/src/data/experiences/*.yaml` (las 9) — `country`,
  logros por nicho, `metricsEstimated` donde aplique.
- `packages/content/src/data/projects/*.yaml` (los 6) —
  `caseStudyDetailed` + `metrics` + `metricsEstimated`.
- `packages/content/src/data/i18n/curriculum/<nicho>.{es,en}.yaml` (×10)
  — `hero.summary` por nicho.
- `packages/content/src/data/profile.ts` — `stats.countries` derivable.
- `packages/content/tests/fixtures/baseline/*.json` — baselines
  actualizados (cambio deliberado de data).
- `packages/app-shared/src/components/CvSections.astro` — enlaces a las
  páginas de detalle desde las tarjetas.
- `packages/app-shared/src/lib/build-stats.ts` — si `countries` pasa a
  derivarse del campo `country`.

### Eliminar

- `docs/specs/b-cv-content-enrichment/` — último commit (Fase 6).

[← README](README.md) · [Fase 1 →](02-fase-schema-zod.md)
