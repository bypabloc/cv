# Fase 1 — Schema: country, metricsEstimated

[← Contexto](01-contexto-y-decision.md) · [Fase 2 →](03-fase-db-migracion.md)

## Objetivo

Preparar `schemas.ts` para los campos nuevos antes de tocar la data.
Cubre AC-1, AC-7 (parte schema).

## Estado actual

`packages/content/src/schemas.ts`:

- `ExperienceSchema` — 13 campos, sin `country`.
- `ProjectSchema` — tiene `caseStudyDetailed?` y `metrics?` opcionales.
- Ningún schema tiene `metricsEstimated`.

## Sub-tareas

### 1.1 — `country` en ExperienceSchema

Agregar tras `company` (es obligatorio: las 9 experiencias lo tendrán):

```ts
company: z.string().min(1),
country: z.string().min(1),
companyUrl: z.string().url().optional(),
```

> Se agrega como obligatorio (no `.optional()`) porque la Fase 2 lo
> llena en las 9. Esto fuerza que ninguna experiencia futura lo omita.

### 1.2 — `metricsEstimated` en ExperienceSchema y ProjectSchema

Campo interno: marca que la entry tiene cifras inventadas pendientes de
validación por el usuario. `default(false)`, opcional en el YAML.

```ts
// en ExperienceSchema y en ProjectSchema:
metricsEstimated: z.boolean().default(false),
```

> `metricsEstimated` NO se renderiza en ningún componente — es un
> marcador de auditoría. El componente de detalle y `CvSections` lo
> ignoran. Sirve para: (a) que el usuario filtre en el anexo qué
> revisar, (b) un futuro test que liste las entries con cifras sin
> confirmar.

### 1.3 — Decisión sobre caseStudyDetailed/metrics

NO se cambia el schema de `ProjectSchema` para estos: siguen
`.optional()`. La Fase 3 los llena en los 6 proyectos por DATA, no por
schema. Razón: marcarlos obligatorios rompería la flexibilidad para un
proyecto futuro tipo "concept" sin case study.

## TDD

`packages/content/tests/unit/schemas-*.test.ts` (extender el que cubra
los schemas):

```ts
it('Given una experiencia con country When ExperienceSchema.parse Then acepta el campo', () => {
  const raw = { /* experiencia minima valida */ country: 'Perú' }
  const parsed = ExperienceSchema.parse(raw)
  expect(parsed.country).toBe('Perú')
})

it('Given una experiencia sin metricsEstimated When parse Then default es false', () => {
  const parsed = ExperienceSchema.parse({ /* sin metricsEstimated */ })
  expect(parsed.metricsEstimated).toBe(false)
})

it('Given un proyecto con metricsEstimated true When parse Then lo conserva', () => {
  const parsed = ProjectSchema.parse({ /* metricsEstimated: true */ })
  expect(parsed.metricsEstimated).toBe(true)
})
```

Red: el schema aún no tiene los campos. Green: agregarlos.

> Al agregar `country` obligatorio, los YAML actuales SIN `country`
> dejan de parsear — los tests de carga de `experiences` fallarán. Esto
> es esperado: la Fase 1 y la Fase 2 van en commits consecutivos y el
> repo queda verde recién al terminar la Fase 2. Alternativa para que la
> Fase 1 deje el repo verde sola: agregar `country` ya con valor a las 9
> en el mismo commit de la Fase 1. **Decisión**: la Fase 1 agrega
> `country` al schema Y a las 9 experiencias con su país (sin tocar el
> resto del contenido). Así el commit 1 deja verde. La reestructuración
> de las 4 + los logros van en la Fase 2.

## Verificación de la fase

```bash
pnpm --filter @portfolio/content exec vitest run
pnpm --filter @portfolio/content run typecheck
```

## Definition of Done de la fase

- [ ] `ExperienceSchema` tiene `country` (obligatorio) y
      `metricsEstimated` (default false).
- [ ] `ProjectSchema` tiene `metricsEstimated` (default false).
- [ ] Las 9 experiencias YAML tienen `country` con su país.
- [ ] `stats.countries` en `profile.ts` deriva del campo (o se confirma
      que sigue siendo 4).
- [ ] Tests del schema verdes; `vitest` content verde.

[← Contexto](01-contexto-y-decision.md) · [Fase 2 →](03-fase-db-migracion.md)
