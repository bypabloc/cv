# Fase 1 — Corregir profile.stats + summary desactualizado

[← Contexto](01-contexto-y-decision.md) · [Fase 2 →](03-fase-profile-niches-db.md)

## Objetivo

Alinear `profile.ts` con la data real: `stats.companies` de 8 a 5, y el
`summary` (es + en) de "8 años" a "12 años" (consistente con
`stats.yearsExperience = 12`, que es correcto). Cubre AC-1, AC-2, AC-3, AC-4.

## Estado actual

`packages/content/src/data/profile.ts`:

```ts
summary: {
  es: '... con más de 8 años de experiencia ...',
  en: '... with over 8 years of experience ...',
},
stats: {
  yearsExperience: 12,   // correcto — se mantiene
  companies: 8,          // INCORRECTO — data real: 5 empresas distintas
  countries: 4,          // correcto — se mantiene, agregar comentario
  certifications: 11,    // correcto (11 YAML en certificates/)
},
```

`packages/app-shared/src/lib/build-stats.ts` ya tiene `countCompanies()`
y `calcYearsExperience()`. `buildStats()` hace short-circuit en
`profile.stats`. El test `packages/app-shared/tests/unit/lib/build-stats.test.ts`
YA existe — se extiende, no se crea.

## TDD: Red → Green → Refactor

### Paso 1 — Red: escribir/extender tests que fallen

En `packages/app-shared/tests/unit/lib/build-stats.test.ts`, asegurar que
existen estos casos con asserts EXACTOS:

```ts
it('Given la data real de experiences When countCompanies Then retorna 5', () => {
  // Act
  const result = countCompanies(experiences)
  // Assert — 5 nombres distintos: Destacame, Dibal, GoodMeal,
  //   Laboratorio Cofasa S.A., Independiente / Académico
  expect(result).toBe(5)
})

it('Given profile.stats presente When buildStats Then retorna los stats declarados', () => {
  // Act
  const result = buildStats()
  // Assert
  expect(result).toEqual({
    yearsExperience: 12,
    companies: 5,
    countries: 4,
    certifications: 11,
  })
})
```

Si el test ya cubre estos casos con otros valores, ACTUALIZARLO a los
valores correctos. Correrlo: debe fallar (Red) porque `profile.ts`
todavía tiene `companies: 8`.

### Paso 2 — Green: corregir profile.ts

En `packages/content/src/data/profile.ts`:

1. `stats.companies`: `8` → `5`.
2. `stats.countries`: agregar comentario inline explicando que es manual:
   ```ts
   // 4 paises: Venezuela (primeras exp), Perú (Dibal),
   //   Chile + México (Destacame, ambas sucursales).
   countries: 4,
   ```
3. `summary.es`: `'más de 8 años de experiencia'` → `'más de 12 años de
   experiencia'`. Revisar el texto completo: el resto del párrafo se
   mantiene, solo cambia la cifra.
4. `summary.en`: `'with over 8 years of experience'` → `'with over 12
   years of experience'`.

Re-correr los tests: deben pasar (Green).

### Paso 3 — Refactor

Verificar que el docstring `@example` de `buildStats` en
`build-stats.ts` ya muestra `companies: 5` (lo muestra). Si algún otro
docstring o comentario del repo cita los stats viejos, alinearlo. No hay
refactor estructural — la lógica de `build-stats.ts` ya estaba bien.

## Verificación de la fase

```bash
pnpm --filter @portfolio/content exec vitest run
pnpm --filter @portfolio/app-shared exec vitest run
pnpm --filter @portfolio/content run typecheck
pnpm --filter @portfolio/app-shared run typecheck
```

Todo verde. Coverage de `build-stats.ts` >= 80%.

## Definition of Done de la fase

- [ ] `profile.ts` tiene `companies: 5`, `countries: 4` con comentario,
      `summary` es/en con "12 años" / "12 years".
- [ ] `build-stats.test.ts` cubre `countCompanies` (== 5) y `buildStats`
      (objeto exacto) y pasa.
- [ ] Typecheck verde en `content` y `app-shared`.
- [ ] Coverage `build-stats.ts` >= 80%.

[← Contexto](01-contexto-y-decision.md) · [Fase 2 →](03-fase-profile-niches-db.md)
