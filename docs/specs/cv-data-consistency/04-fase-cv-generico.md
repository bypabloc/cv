# Fase 3 — Enriquecer el render del CV genérico

[← Fase 2](03-fase-profile-niches-db.md) · [Commits →](05-commits.md)

## Objetivo

El CV genérico (`apps/generic`, `niche === 'generic'`) debe mostrar el
CV completo; los 4 CV de nicho un subset. Hoy `CvSections.astro` recorta
`responsibilities` a 3 para TODAS las apps y NUNCA muestra `achievements`.
Reorganizar el render para diferenciar. Cubre AC-9, AC-10.

## Estado actual

`packages/app-shared/src/components/CvSections.astro`, sección
`#experience` (líneas ~228-270):

```astro
{exps.map((e, idx) => (
  <TimelineItem role={...} company={...} ...>
    <ul class="exp-bullets">
      {e.responsibilities[locale].slice(0, 3).map((r) => (
        <li>{r}</li>
      ))}
    </ul>
  </TimelineItem>
))}
```

Problemas:

1. `slice(0, 3)` aplica a todas las apps — el CV genérico también
   recorta. Cada experiencia tiene 6-13 responsibilities reales en el
   YAML; se muestran solo 3.
2. `e.achievements` NO se renderiza nunca. Cada experiencia tiene 7-13
   achievements (logros con métricas) en el YAML — data escrita que no
   se ve en ningún CV.

`niche` ya está disponible en el componente (`Astro.props`). El schema
`Experience` tiene `responsibilities {es,en}` y `achievements {es,en}`,
ambos arrays de string.

## Sub-tareas

### 3.1 — Decidir el corte (helper testeable)

Para que la lógica sea testeable con Vitest (los `.astro` no se renderizan
en happy-dom), extraer una función pura a
`packages/app-shared/src/lib/cv-detail.ts`:

```ts
/**
 * @module cv-detail
 * @description Decide el nivel de detalle del CV según el niche. El CV
 *   genérico muestra todo; los niches un subset.
 */
import type { Niche } from '@portfolio/content'

/** Máximo de responsibilities en un CV de niche. El genérico no recorta. */
export const NICHE_RESPONSIBILITIES_LIMIT = 3

/**
 * @function isDetailedCv
 * @description True si el CV debe mostrar el detalle completo
 *   (responsibilities sin recorte + achievements). Solo el genérico.
 */
export function isDetailedCv(niche: Niche): boolean {
  return niche === 'generic'
}

/**
 * @function visibleResponsibilities
 * @description Responsibilities a mostrar según el niche: todas para el
 *   genérico, las primeras NICHE_RESPONSIBILITIES_LIMIT para un niche.
 */
export function visibleResponsibilities(
  items: readonly string[],
  niche: Niche,
): readonly string[] {
  return isDetailedCv(niche)
    ? items
    : items.slice(0, NICHE_RESPONSIBILITIES_LIMIT)
}
```

### 3.2 — TDD: tests del helper

`packages/app-shared/tests/unit/lib/cv-detail.test.ts` (crear):

```ts
it('Given niche generic When isDetailedCv Then true', () => {
  expect(isDetailedCv('generic')).toBe(true)
})

it('Given niche architect When isDetailedCv Then false', () => {
  expect(isDetailedCv('architect')).toBe(false)
})

it('Given 5 items y niche generic When visibleResponsibilities Then retorna los 5', () => {
  const items = ['a', 'b', 'c', 'd', 'e']
  expect(visibleResponsibilities(items, 'generic')).toEqual([
    'a', 'b', 'c', 'd', 'e',
  ])
})

it('Given 5 items y niche fintech When visibleResponsibilities Then retorna los primeros 3', () => {
  const items = ['a', 'b', 'c', 'd', 'e']
  expect(visibleResponsibilities(items, 'fintech')).toEqual(['a', 'b', 'c'])
})
```

Red: el archivo `cv-detail.ts` no existe → falla. Green: crear el helper.

### 3.3 — Usar el helper en CvSections.astro

En `CvSections.astro`:

1. Importar: `import { isDetailedCv, visibleResponsibilities } from
   '../lib/cv-detail'`.
2. En el `.map()` de `#experience`, reemplazar el `<ul>`:

```astro
{exps.map((e, idx) => (
  <TimelineItem role={...} company={...} ...>
    <ul class="exp-bullets">
      {visibleResponsibilities(e.responsibilities[locale], niche).map((r) => (
        <li>{r}</li>
      ))}
    </ul>
    {isDetailedCv(niche) && e.achievements[locale].length > 0 && (
      <>
        <p class="exp-achievements__heading text-label">
          {t.labels.achievements}
        </p>
        <ul class="exp-bullets exp-bullets--achievements">
          {e.achievements[locale].map((a) => (
            <li>{a}</li>
          ))}
        </ul>
      </>
    )}
  </TimelineItem>
))}
```

3. Agregar el estilo `.exp-achievements__heading` + `.exp-bullets--achievements`
   en el bloque `<style>` (tokens del DS, sin hex inline).

### 3.4 — Label i18n `achievements`

El render usa `t.labels.achievements`. Verificar si ya existe en
`packages/content/src/data/i18n/elements/elements.{es,en}.yaml` (bloque
`labels`). La auditoría reportó `labels` con muchas keys
(`technicalSkills`, `softSkills`, ...). Si `achievements` NO existe:

- `elements.es.yaml`: `labels.achievements: "Logros"`.
- `elements.en.yaml`: `labels.achievements: "Achievements"`.
- Verificar que el schema `ElementsStringsSchema` en `schemas.ts` admite
  la key nueva (si `labels` es un objeto cerrado, agregar el campo al
  schema; si es `z.record`, no hace falta).

> Si ya existe `labels.achievements` (probable — hay sección
> `sections.experience` y labels de skills), reutilizarlo y saltar 3.4.

## Verificación de la fase

```bash
pnpm --filter @portfolio/app-shared exec vitest run
pnpm --filter @portfolio/content exec vitest run
pnpm --filter @portfolio/app-shared run typecheck
pnpm exec biome check packages/app-shared packages/content
pnpm run build
pnpm run preview   # verificar visualmente: generic muestra todo,
                   #   un niche muestra subset
```

## Definition of Done de la fase

- [ ] `cv-detail.ts` creado con `isDetailedCv` + `visibleResponsibilities`
      + `NICHE_RESPONSIBILITIES_LIMIT`.
- [ ] `cv-detail.test.ts` cubre los 4 casos, coverage >= 80%.
- [ ] `CvSections.astro` usa el helper; el genérico muestra
      responsibilities completas + achievements; los niches el subset.
- [ ] Label `achievements` existe en `elements.{es,en}.yaml` (o se
      reutiliza el existente).
- [ ] `biome check` + typecheck + `astro check` verdes.
- [ ] `pnpm run build` compila las 6 apps.
- [ ] Preview visual: diferencia generic vs niche confirmada.

[← Fase 2](03-fase-profile-niches-db.md) · [Commits →](05-commits.md)
