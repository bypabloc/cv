# Fase 6 — Páginas de detalle por experiencia y proyecto

[← Fase 5](06-fase-summary-nicho.md) · [Commits →](08-commits.md)

## Objetivo

Crear páginas de detalle `/experience/<slug>` y `/projects/<slug>` en las
6 apps, con enlaces desde las tarjetas del home. Cubre AC-11, AC-12,
AC-13.

## Estado actual

- Las 6 apps tienen solo `index`, `about`, `certificates`, `contact`
  (+ `en/`). **No hay rutas dinámicas.**
- Patrón de página: thin wrapper por app + componente compartido de
  `packages/app-shared/`. Ejemplo real (`apps/generic/src/pages/about.astro`):
  ```astro
  ---
  import AboutSection from '@portfolio/app-shared/pages/AboutSection.astro'
  import PageLayout from '../layouts/PageLayout.astro'
  import { NICHE, STRINGS } from '../lib/site-config'
  const t = STRINGS.es
  ---
  <PageLayout title={...} canonicalPath="/about" locale="es"
    otherLocalePath="/en/about">
    <AboutSection niche={NICHE} locale="es" strings={t} />
  </PageLayout>
  ```
- La data viene de `@portfolio/content` (`import { experiences,
  projects }`). **NO hay content collections de Astro** — `getStaticPaths`
  usa ese import, NUNCA `getCollection()`.
- `CvSections.astro` renderiza las tarjetas de experiencia
  (`TimelineItem`) y de proyecto (`ProjectBentoCard`).

## Sub-tareas

### 6.1 — Componente `ExperienceDetail.astro` (app-shared)

`packages/app-shared/src/components/ExperienceDetail.astro` — vista
completa de una experiencia: rol, empresa, país, fechas, TODAS las
responsabilidades, TODOS los logros, skills. Props:

```ts
interface Props {
  experience: Experience
  locale: 'es' | 'en'
  strings: I18nStrings
}
```

Reusa labels existentes (`t.labels.responsibilities`,
`t.labels.achievements` — agregados en el plan A). NO renderiza
`metricsEstimated` (es interno).

### 6.2 — Componente `ProjectDetail.astro` (app-shared)

`packages/app-shared/src/components/ProjectDetail.astro` — vista completa
de un proyecto: nombre, summary, descripción, stack, links (url/repo),
`caseStudyDetailed` (problem/process/result) y `metrics`. Reusa
`CaseStudyExpander` o renderiza el case study expandido. Props análogas.

### 6.3 — Rutas dinámicas en las 6 apps

Por cada app, 4 archivos nuevos:

```text
apps/<app>/src/pages/experience/[slug].astro
apps/<app>/src/pages/en/experience/[slug].astro
apps/<app>/src/pages/projects/[slug].astro
apps/<app>/src/pages/en/projects/[slug].astro
```

Patrón de `experience/[slug].astro` (thin wrapper + `getStaticPaths`):

```astro
---
import { experiences } from '@portfolio/content'
import ExperienceDetail from '@portfolio/app-shared/components/ExperienceDetail.astro'
import PageLayout from '../../layouts/PageLayout.astro'
import { NICHE, STRINGS } from '../../lib/site-config'

export function getStaticPaths() {
  return experiences.map((exp) => ({
    params: { slug: exp.slug },
    props: { experience: exp },
  }))
}

const { experience } = Astro.props
const t = STRINGS.es
---
<PageLayout
  title={`${experience.role.es} — ${experience.company}`}
  description={`${experience.role.es} en ${experience.company}, ${experience.country}`}
  canonicalPath={`/experience/${experience.slug}`}
  locale="es"
  otherLocalePath={`/en/experience/${experience.slug}`}
>
  <ExperienceDetail experience={experience} locale="es" strings={t} />
</PageLayout>
```

La variante `en/experience/[slug].astro` es idéntica con `locale="en"`,
`STRINGS.en`, paths con prefijo `/en`. `projects/[slug].astro` análogo
con `projects` y `ProjectDetail`.

> Las 6 apps comparten los componentes `ExperienceDetail`/`ProjectDetail`
> de `app-shared`. Cada app solo tiene el thin wrapper (que aporta su
> `NICHE`, `STRINGS`, `PageLayout`). 24 archivos thin wrapper en total
> (4 × 6 apps), todos casi idénticos.

> **Todas** las experiencias y proyectos tienen página de detalle, en
> las 6 apps — incluso los que un nicho no destaca (D-3, D-6). El filtro
> por nicho afecta qué se ve en el HOME, no qué páginas de detalle
> existen.

### 6.4 — Enlaces desde las tarjetas (CvSections.astro)

En `packages/app-shared/src/components/CvSections.astro`:

- Cada `TimelineItem` (experiencia) recibe un enlace a
  `/experience/<slug>` (con prefijo `/en` según locale).
- Cada `ProjectBentoCard` recibe un enlace a `/projects/<slug>`.
- D-3: las experiencias antiguas no-relevantes al nicho se muestran al
  final como **tarjeta resumen** (rol + empresa + país + fechas + 1
  línea) con botón "Ver detalle". Esto requiere:
  - un helper que separe, para un nicho, las experiencias "destacadas"
    de las "previas" (ej. por umbral de `priority` o por pertenencia al
    `niches[]` del nicho actual);
  - un modo compacto de tarjeta (puede ser un prop nuevo de
    `TimelineItem` o un componente `ExperienceSummaryCard`).

> Revisar si `TimelineItem` y `ProjectBentoCard` ya aceptan un prop
> `href`/`detailUrl`. Si no, agregarlo (cambio mínimo, retrocompatible
> con default opcional).

### 6.5 — getStaticPaths y output estático

Las apps son `output: 'static'`. `getStaticPaths` se evalúa en build y
genera el HTML de cada slug. Total:
9 experiencias × 2 locales × 6 apps + 7 proyectos × 2 locales × 6 apps =
**192 páginas estáticas nuevas**. El build debe seguir completando en
tiempo razonable (verificar en la Fase 7).

## Verificación de la fase

```bash
pnpm --filter @portfolio/app-shared run typecheck
pnpm exec biome check packages/app-shared apps
pnpm run build
pnpm run preview   # navegar a /experience/<slug> y /projects/<slug>
```

Verificar en el `dist` de cada app que existen las carpetas
`experience/<slug>/` y `projects/<slug>/` con su `index.html`, en es y
en `en/`.

## Definition of Done de la fase

- [ ] `ExperienceDetail.astro` y `ProjectDetail.astro` creados en
      `app-shared`.
- [ ] Las 6 apps tienen las 4 rutas dinámicas (`experience/[slug]`,
      `projects/[slug]`, en es y en).
- [ ] El home enlaza cada tarjeta a su página de detalle.
- [ ] Las experiencias antiguas no-relevantes al nicho se muestran como
      tarjeta resumen + botón al detalle.
- [ ] `pnpm run build` genera las ~192 páginas sin error.
- [ ] `biome` + typecheck + `astro check` verdes.

[← Fase 5](06-fase-summary-nicho.md) · [Commits →](08-commits.md)
