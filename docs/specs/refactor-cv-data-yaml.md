# Refactor: CV data a patrón híbrido TypeScript + YAML

> Spec del refactor de `packages/content/src/data/*.ts` (10 archivos monolíticos)
> a un patrón YAML-as-source + TS-as-orchestrator. La API pública del package no
> cambia: consumers siguen haciendo `import { experiences } from '@portfolio/content'`.

**Fecha**: 2026-05-13
**Estado**: in_progress
**Branch**: `feature/cv-modern-impactful-redesign` (refactor incluido)
**Alcance**: monorepo completo (`packages/content/`, `packages/app-shared/`,
`packages/cv-pdf/`, 6 apps, rules, CLAUDE.md)
**Estrategia**: secuencial T1 → T2 → T3 → T4 → T5 en una sesión.

---

## 1. Contexto / Problema

La data del CV vive hoy en `packages/content/src/data/*.ts` con arrays inline.

- **Archivos monolíticos**: `experiences.ts` 430 líneas, `projects.ts` 248,
  `skills.ts` 174.
- **Bilingüe inline**: cada entry mezcla `{es, en}` dentro del .ts, ruidoso en
  diffs y difícil para edición no-técnica.
- **Schemas inconsistentes**: Education, Reference, Language no tienen
  `niches[]` (intencional pero indocumentado).
- **Sin tests**: `build-stats` y el helper nuevo `load-yaml-entries`.
- **`site-config.ts` duplicado** en las 6 apps (~50 líneas cada uno, 80% del
  cuerpo son overrides repetidos).

### Hallazgos de exploración

- Patrón actual sólido: `filterByNiche` + `sortByPriority` ya están centralizados
  en `packages/content/src/lib/` con tests 100% coverage.
- 0 `any` en el package — la migración debe preservar ese estándar.
- Workspace externo bloquea Content Collections: Astro 6 Content Collections solo
  soporta data dentro de `apps/<X>/src/content/`. Para mantener fuente única en
  `packages/content/` se usa el patrón híbrido (`vite-plugin-yaml` +
  `import.meta.glob` + Zod manual).

---

## 2. Solución Propuesta

Migrar `packages/content/src/data/*.ts` a un patrón **YAML-as-source +
TS-as-orchestrator**:

- YAML = fuente de datos (1 archivo por entry, slug-based filename).
- TS = orquestador que glob-importa los YAML, valida con Zod, exporta array
  tipado readonly.
- Zod schemas permanecen como contrato (única fuente de verdad de tipos).
- API pública del package no cambia.

### Decisiones clave (aprobadas)

- **D1**: Patrón híbrido TS+YAML (no Content Collections), fuente única en
  `packages/content/`.
- **D2**: 1 YAML por entry, filename = slug.
- **D3**: Bilingüe `{es, en}` inline en cada YAML (no separar por locale).
- **D4**: Tests obligatorios para `lib/` con coverage ≥ 80%.
- **D5**: `niches?: Niche[]` opcional en Education/Reference/Language.
- **D6**: `site-config.ts` por app NO se elimina (solo se reduce con
  `defineSiteConfig`).
- **D7**: `@modyfi/vite-plugin-yaml` en 8 lugares (6 apps + cv-pdf + vitest).

---

## 3. Criterios de Aceptación (AC)

- **AC-1**: Given el package `@portfolio/content`, When se importan
  `experiences`, `projects`, `certificates`, `publications`, `awards`,
  `skills`, `education`, `references`, `languages`, `profile`, Then todas
  retornan arrays/objects con los mismos shapes y mismo contenido que antes
  del refactor (snapshot baseline).
- **AC-2**: Given un YAML inválido en
  `packages/content/src/data/<entity>/<slug>.yaml`, When se ejecuta
  `pnpm run build` en cualquier app, Then el build falla con error Zod
  identificando el archivo y el campo.
- **AC-3**: Given el slug `destacame-architect.yaml`, When la entry se carga,
  Then `entry.slug === 'destacame-architect'` (slug derivado del filename,
  validado contra el campo `slug` del YAML).
- **AC-4**: Given `filterByNiche(experiences, 'fintech')`, When se ejecuta en
  runtime, Then retorna el mismo subset que antes del refactor (verificable
  via snapshot del array de slugs).
- **AC-5**: Given `pnpm exec vitest run --coverage` en `packages/content/` y
  `packages/app-shared/`, When se ejecuta, Then coverage per-file ≥ 80% en
  `src/lib/*.ts`.
- **AC-6**: Given `pnpm run build` en cada una de las 6 apps, When se ejecuta,
  Then completa exitosamente y los `dist/` resultantes contienen el CV
  renderizado idéntico al pre-refactor.
- **AC-7**: Given `pnpm --filter @portfolio/cv-pdf run generate -- --niche fintech --out tmp/`,
  When se ejecuta, Then genera `cv.html` con contenido idéntico al
  pre-refactor.
- **AC-8**: Given el schema actualizado de Education/Reference/Language, When
  un YAML omite `niches`, Then la entry parsea correctamente (campo opcional).
- **AC-9** (revisado durante ejecucion): Given el helper `defineSiteConfig`
  en `app-shared`, When una app lo usa, Then `apps/<app>/src/lib/site-config.ts`
  reduce boilerplate (NICHE + SITE_URL + OG_IMAGE + STRINGS hidden detrás de
  un solo factory). El cuerpo del override (~25-40 lineas de strings) NO se
  toca porque cada string es legitimamente unico por sitio (meta titles,
  ATS keywords). Verificable por: una sola llamada `defineSiteConfig({...})`
  por app, sin declarar manualmente `NICHE`, `SITE_URL`, `OG_IMAGE`.

---

## 4. Descomposición en tareas (T1-T5, secuencial)

| Tarea | Resumen | AC cubiertos |
|-------|---------|--------------|
| **T1** | Helper `load-yaml-entries` + schemas (niches opcional) + tests TDD + deps `@modyfi/vite-plugin-yaml` | AC-2, AC-3, AC-5, AC-8 |
| **T2** | Migrar experiences (9), projects (7), skills (10) a YAML + index.ts orquesta | AC-1, AC-3, AC-4 (partial) |
| **T3** | Migrar certificates (11), publications (5), awards (2) a YAML + index.ts | AC-1, AC-4 (partial) |
| **T4** | Migrar education (3), references (10), languages (2) a YAML + index.ts | AC-1, AC-8 |
| **T5** | `defineSiteConfig` en `app-shared` + 6 `apps/<app>/astro.config.ts` + 6 `site-config.ts` + cv-pdf + rule `.claude/rules/yaml-data-loading.md` + CLAUDE.md | AC-6, AC-7, AC-9 |

---

## 5. Definition of Done

- [ ] AC-1: snapshot baseline (10 arrays) matches post-refactor.
- [ ] AC-2: Zod error identifica filename + field cuando YAML rompe.
- [ ] AC-3: filename slug === YAML.slug enforced (test cubre el fallo).
- [ ] AC-4: `filterByNiche` snapshot por niche × entidad pasa.
- [ ] AC-5: coverage ≥ 80% per-file en `packages/content/src/lib/*` y
  `packages/app-shared/src/lib/*`.
- [ ] AC-6: `pnpm run build` exitoso en las 6 apps.
- [ ] AC-7: `cv-pdf generate` produce HTML idéntico (diff vs baseline).
- [ ] AC-8: Education/Reference/Language schema permite `niches?` opcional.
- [ ] AC-9: 6 `apps/<app>/src/lib/site-config.ts` ≤ 20 líneas cada uno.
- [ ] Typecheck pasa: `pnpm exec tsc --noEmit` + `pnpm exec astro check`.
- [ ] Conformance pasa: `pnpm exec biome check .`.
- [ ] Rule nueva validada con `claude -p` en 5 prompts.
- [ ] `CLAUDE.md` actualizado con link a la rule nueva.
- [ ] `tmp/cv-baseline/` y snapshots intermedios eliminados antes del commit
  final (o gitignoreados).

---

## 6. Anexos

- Reporte de exploración: [tmp/explore_cv_contexts_refactor.md](../../tmp/explore_cv_contexts_refactor.md)
- Reporte de research técnico (YAML loaders, Content Collections): conversación
  de sesión, no persistido a disco.

---

**Última actualización**: 2026-05-13
