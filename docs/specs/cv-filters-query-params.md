# Plan: CV Filters via Query Params

> Plan Large (~30+ archivos). Filtros client-side sobre el CV con URL params
> compartibles, sincronizados con UI de chips. Aplica a las 6 apps del
> monorepo (generic, hub, fintech, architect, leader, vibe), en
> `/about` (es/en) y en `cv*.html` publicos.

## 1. Contexto / Problema

El CV del portfolio se renderiza hoy en dos superficies por app:

- **Pagina web** (`apps/*/src/pages/about.astro`, version es y en)
- **CV HTML publico** descargable (`public/cv.html`, `cv-es.html`, `cv-en.html`)

Ambas son 100% SSG estaticas, filtradas en build-time por el `niche` fijo
de cada app via `filterByNiche()` + `sortByPriority()`. No hay
interactividad: un visitante solo puede leer la version pre-filtrada.

Necesidad: permitir a un visitante (recruiter, tech lead) refinar lo que
ve segun sus intereses (ej. solo proyectos Vue, solo experiencia ultimos
3 anos, solo skills tecnicas), via URL params compartibles y chips
visibles. Sin cambiar el niche de la app (eso ya lo cubren los subdominios).

### Hallazgos de exploracion (2026-05-13)

- `filterByNiche()`, `sortByPriority()`, `buildStats()` viven en
  `packages/content/src/lib/` y operan sobre objetos ya cargados (data
  es YAML hibrido tras commit `cf21586`).
- `CvSections.astro` y `AboutSection.astro` en `packages/app-shared/src/`
  ya aceptan `niche` como prop dinamico (no hardcoded).
- `renderCvHtml({ locale, niche })` en `packages/cv-pdf/src/lib/` acepta
  niche dinamico.
- Schemas en `packages/content/src/schemas.ts` no tienen hoy `seniority`
  en experiences ni `projectType` en projects. Hay que agregarlos.
- Cero JS client-side en CV hoy. La spec E2E `cv-screenshots.spec.ts`
  confirma que el CV es 100% estatico.
- Cada app genera 3 CV HTML (cv.html / cv-es.html / cv-en.html) via
  `scripts/build-public-assets.mjs`. Hub no genera CV HTML (no tiene
  about.astro propio, es selector).

## 2. Solucion Propuesta

**Arquitectura**: vanilla JS (~5-8kb gzip) que opera sobre `data-*`
attributes serializados en build. Sin frameworks reactivos. ATS-safe
por diseno (HTML completo en disco, JS solo decora).

**Pipeline**:

```text
build-time (SSG)
  data YAML
    -> filterByNiche(app niche)  -> data ya filtrada por niche
    -> renderiza HTML con data-* en cada item
    -> embebe <script type="application/json" id="cv-data"> con data serializada
client-time (cuando hay query params o el visitante interactua)
  cv-filters.js lee URLSearchParams
    -> aplica display:none a items no-match
    -> recalcula stats con buildStats client-side
    -> sincroniza UI chips con estado actual
    -> actualiza URL via history.replaceState
```

### Decisiones clave

- **Decision 1: vanilla JS sin framework** — coherente con el patron
  "cero JS en CV" del proyecto. Footprint minimo (~5-8kb). Sin Preact/Solid.
- **Decision 2: data-attributes en HTML + JSON embebido** — los chips
  filtran via `[data-tech]`, `[data-seniority]`, etc. El JSON embebido
  permite recalcular `buildStats()` client-side sin re-fetch.
- **Decision 3: filtros operan DENTRO del niche fijo de cada app** —
  el niche NO es cambiable via URL. La identidad por subdominio se
  preserva. Filtros son refinamiento, no cambio de identidad.
- **Decision 4: NUEVOS campos de schema obligatorios** — `seniority`
  (5 valores) en experiences y `projectType` (6 valores) en projects.
  Backfill obligatorio antes de habilitar filtros. Sin backfill el filtro
  no tiene sentido.
- **Decision 5: `<noscript>` fallback** — el JS solo decora. Sin JS, el
  CV se ve completo (ATS-safe). Por lo tanto, los chips se renderizan
  como `<noscript>` ocultos para no contaminar la version estatica.
  Los chips visibles aparecen via JS al cargar.
- **Decision 6: implementacion full en las 6 apps simultaneamente** —
  un solo PR coherente. Permite agentes paralelos en worktrees por app.
- **Decision 7: hub queda fuera del scope CV** — hub es selector
  multi-app, no tiene `about.astro` ni cv\*.html. Si en el futuro
  hub agrega CV, replicar el patron.

## 3. Criterios de Aceptacion (AC)

Formato BDD. Cada test debera referenciar al menos uno de estos.

### Schema y data

- **AC-1**: Given una experience en `packages/content/src/data/experiences/*.yaml`, When se carga via `loadYamlEntries()`, Then `seniority` esta presente y es uno de `intern|junior|mid|senior|lead`.
- **AC-2**: Given un project en `packages/content/src/data/projects/*.yaml`, When se carga, Then `projectType` esta presente y es uno de `web|mobile|cli|library|ai|fintech-platform`.
- **AC-3**: Given los 9 experiences y N projects existentes, When se valida el schema, Then todos tienen `seniority` y `projectType` respectivamente (backfill completo).

### Filter engine (JS)

- **AC-4**: Given `?tech=Vue,Django` en URL, When carga la pagina, Then solo items con `data-tech` que contenga "Vue" O "Django" quedan visibles (OR logico intra-dimension).
- **AC-5**: Given `?tech=Vue&seniority=senior` en URL, When carga, Then solo items que matchean ambas dimensiones quedan visibles (AND logico inter-dimension).
- **AC-6**: Given `?from=2022-01&to=2026-05` en URL, When carga, Then solo items cuyo rango `[data-start, data-end]` intersecta con `[2022-01, 2026-05]` queda visible.
- **AC-7**: Given `?skills=technical` en URL, When carga, Then solo bloques de skills con `data-skill-kind="technical"` quedan visibles.
- **AC-8**: Given `?hideConfidential=1` en URL, When carga, Then items con `data-confidential="true"` se ocultan.
- **AC-9**: Given una URL sin query params, When carga, Then TODOS los items son visibles (default = sin filtro).
- **AC-10**: Given un param invalido (ej. `?seniority=invalid`), When carga, Then se ignora silenciosamente sin romper el filtro.

### UI chips + URL sync

- **AC-11**: Given chips renderizados en la pagina, When el usuario clickea un chip, Then la URL se actualiza via `history.replaceState` SIN recargar la pagina.
- **AC-12**: Given URL con params al cargar, When el JS se inicializa, Then los chips reflejan el estado activo (chip seleccionado tiene clase `is-active`).
- **AC-13**: Given filtros activos, When el usuario clickea "Limpiar filtros", Then todos los items vuelven visibles y la URL queda sin query string.

### Stats dinamicos

- **AC-14**: Given filtros activos que reducen experiences visibles, When se recalculan stats, Then `years exp`, `empresas`, `paises` reflejan SOLO los items visibles.
- **AC-15**: Given filtros que dejan 0 items visibles en un seccion, When se renderiza, Then aparece mensaje "No hay items con estos filtros" en lugar de la seccion vacia.

### ATS-safe / SSR fallback

- **AC-16**: Given JS desactivado en el browser, When se carga el CV, Then TODOS los items son visibles (los chips no aparecen, no hay filtrado).
- **AC-17**: Given un ATS scraper que descarga `cv-es.html`, When parsea el HTML, Then ve TODO el contenido (no hay items con `display:none` aplicado en el HTML estatico, solo via JS runtime).
- **AC-18**: Given el HTML estatico, When se inspecciona, Then los chips estan ocultos por defecto (`hidden` attribute o CSS `display:none` removido por JS al inicializar).

### Cross-locale + cross-app

- **AC-19**: Given filtros activos en `/about?tech=Vue`, When el usuario cambia a `/en/about`, Then los filtros se preservan (mismo query string).
- **AC-20**: Given que el feature se implementa en las 6 apps (excepto hub), When se navega a `fintech.localhost:9970/about?tech=Vue`, Then los filtros funcionan igual que en `architect.localhost:9970/about?tech=Vue`.

## 4. Diagrama de Flujo

### Antes

```text
Build:
  YAML data
    -> filterByNiche(app.niche)
    -> renderiza HTML completo
    -> escribe public/cv.html

Runtime:
  Usuario carga /about
    -> Astro sirve HTML pre-filtrado (estatico)
    -> Sin interactividad
```

### Despues

```text
Build:
  YAML data (incluye seniority + projectType nuevos)
    -> filterByNiche(app.niche)
    -> renderiza HTML con data-* attrs en cada item
    -> embebe <script type="application/json" id="cv-data">
    -> incluye <script src="/cv-filters.js" defer>
    -> escribe public/cv.html + carga FilterChips.astro oculto

Runtime:
  Usuario carga /about (o cv.html)
    -> Astro sirve HTML completo
    -> cv-filters.js inicializa
       -> lee URLSearchParams
       -> {hayParams?} -> Si -> aplica filtros (oculta items no-match)
       -> activa chips UI (display:block)
       -> sincroniza estado chips con URL
       -> recalcula stats si hay filtros
    -> Usuario clickea chip
       -> filter engine recalcula
       -> aplica display:none a items
       -> history.replaceState actualiza URL
       -> recalcula stats
```

## 5. Diagrama ER (schema changes)

### Antes

```text
ExperienceSchema {
  role: string
  company: string
  start: string (YYYY-MM)
  end?: string
  niches: Niche[]
  priority: Record<Niche, number>
  skillsTechnical: string[]
  skillsSoft: string[]
  responsibilities: I18n
  achievements: I18n
}

ProjectSchema {
  name: string
  slug: string
  niches: Niche[]
  priority: Record<Niche, number>
  stack: string[]
  status: 'active' | 'inactive' | 'concept'
  caseStudyDetailed?: { problem, process, result }
  metrics?: Record<string, string>
  isConfidential?: boolean
  url?: string
  repo?: string
}
```

### Despues

```text
ExperienceSchema {
  ... (todos los campos previos)
  seniority: 'intern' | 'junior' | 'mid' | 'senior' | 'lead'  (NUEVO, obligatorio)
}

ProjectSchema {
  ... (todos los campos previos)
  projectType: 'web' | 'mobile' | 'cli' | 'library' | 'ai' | 'fintech-platform'  (NUEVO, obligatorio)
}
```

## 6. Tests Requeridos

### 6.A. TDD Flows (filter engine, logica pura en `public/cv-filters.js` o `packages/cv-filters/src/`)

Escribir antes de implementar:

- WHEN URLSearchParams es `tech=Vue,Django` THEN filterEngine.parse() retorna `{ tech: ['Vue','Django'] }` [AC-4]
- WHEN un item tiene `data-tech="Vue,Astro"` y filtro es `tech=['Vue','Django']` THEN matchesFilter() retorna true [AC-4]
- WHEN item con `data-tech="Python"` y filtro `tech=['Vue','Django']` THEN matchesFilter() retorna false [AC-4]
- WHEN filtros son `{ tech: ['Vue'], seniority: ['senior'] }` y item tiene tech=Vue + seniority=junior THEN matchesFilter() retorna false (AND inter-dimension) [AC-5]
- WHEN rango filtro `[2022-01, 2026-05]` e item `[2020-01, 2024-01]` THEN rangesIntersect() retorna true [AC-6]
- WHEN URL params son `?seniority=invalid` THEN parse() retorna `{ seniority: [] }` (sanitizado) [AC-10]
- WHEN aplicar filtros con 0 matches en una seccion THEN renderEmptyState() inyecta mensaje [AC-15]
- WHEN buildStats client-side se llama con items filtrados THEN retorna `{ years: 3, companies: 2, countries: 2 }` (calculado dinamico) [AC-14]

### 6.B. Unit Tests (Vitest, mirror de `src/`)

Path mirroring:

- `packages/content/src/schemas.ts` -> `packages/content/tests/unit/schemas.test.ts` (validar nuevos campos seniority, projectType) [AC-1, AC-2]
- `packages/content/src/data/experiences/` -> validar que todos los YAML tienen seniority [AC-3]
- `packages/cv-filters/src/parse-params.ts` -> `packages/cv-filters/tests/unit/parse-params.test.ts` [AC-4, AC-10]
- `packages/cv-filters/src/matches-filter.ts` -> idem [AC-4, AC-5, AC-6, AC-7, AC-8]
- `packages/cv-filters/src/ranges-intersect.ts` -> idem [AC-6]
- `packages/cv-filters/src/build-stats-client.ts` -> idem [AC-14]
- `packages/app-shared/src/components/FilterChips.astro` -> test render con props [AC-11, AC-12]

Coverage v8 >= 80% per-file en todos los archivos nuevos.

### 6.C. Typecheck

- `pnpm exec tsc --noEmit` en `packages/content/`, `packages/cv-filters/`, `packages/app-shared/`
- `pnpm exec astro check` en cada app (6 apps)

### 6.D. E2E Tests (Playwright)

Nueva spec: `tests/feature/smoke/cv-filters.spec.ts`

- WHEN navego a `fintech.localhost:9970/about?tech=Vue` THEN solo proyectos con Vue son visibles [AC-4, AC-20]
- WHEN clickeo chip "Senior" THEN URL se actualiza a `?seniority=senior` sin reload [AC-11]
- WHEN clickeo "Limpiar filtros" THEN URL queda sin params y todos los items visibles [AC-13]
- WHEN cargo `?from=2022-01&to=2026-05` THEN solo experiences en ese rango son visibles [AC-6]
- WHEN tengo JS desactivado (browser context con `javaScriptEnabled: false`) THEN todos los items son visibles, chips ocultos [AC-16]
- WHEN navego `/about?tech=Vue` y cambio a `/en/about` THEN filtros persisten [AC-19]

Actualizar spec existente:

- `tests/feature/smoke/cv-screenshots.spec.ts` - agregar 2 screenshots adicionales por niche: uno con filtros activos, otro sin filtros (validar layout no se rompe).

## 7. Archivos Afectados

### Crear

#### Nuevo paquete `packages/cv-filters/`

- `packages/cv-filters/package.json` — workspace package config
  - Verificar: `pnpm install` resuelve workspaces sin warnings
- `packages/cv-filters/tsconfig.json` — extends strict
  - Verificar: `pnpm exec tsc --noEmit` desde el package
- `packages/cv-filters/biome.json` — extends raiz
- `packages/cv-filters/src/types.ts` — `FilterState`, `FilterParams`, `Dimension`
  - Verificar: `pnpm exec tsc --noEmit`
- `packages/cv-filters/src/parse-params.ts` — `parseParams(searchParams: URLSearchParams): FilterState`
  - Verificar: `pnpm exec vitest run tests/unit/parse-params.test.ts`
- `packages/cv-filters/src/matches-filter.ts` — `matchesFilter(item, state): boolean`
  - Verificar: tests AC-4, AC-5, AC-7, AC-8
- `packages/cv-filters/src/ranges-intersect.ts` — `rangesIntersect(a, b): boolean`
  - Verificar: tests AC-6
- `packages/cv-filters/src/build-stats-client.ts` — port de `buildStats()` a client
  - Verificar: tests AC-14
- `packages/cv-filters/src/apply-filters.ts` — orquestador DOM: oculta items, actualiza stats, sincroniza chips
  - Verificar: integracion en spec E2E
- `packages/cv-filters/src/sync-url.ts` — `syncUrl(state)`, `readUrl(): FilterState`
  - Verificar: tests AC-11
- `packages/cv-filters/src/index.ts` — entrypoint, exports
- `packages/cv-filters/src/cv-filters.bundle.ts` — bundle iife para uso vanilla en `<script>`
  - Verificar: build produce `dist/cv-filters.js` (~5-8kb gzip)
- `packages/cv-filters/tests/unit/parse-params.test.ts` — AC-4, AC-10
- `packages/cv-filters/tests/unit/matches-filter.test.ts` — AC-4, AC-5, AC-7, AC-8
- `packages/cv-filters/tests/unit/ranges-intersect.test.ts` — AC-6
- `packages/cv-filters/tests/unit/build-stats-client.test.ts` — AC-14
- `packages/cv-filters/tests/unit/sync-url.test.ts` — AC-11

#### Componentes compartidos nuevos en `packages/app-shared/`

- `packages/app-shared/src/components/FilterChips.astro` — UI de chips, `hidden` por defecto
  - Verificar: `pnpm exec astro check`
- `packages/app-shared/src/components/FilterEmptyState.astro` — mensaje "no hay items con estos filtros"
- `packages/app-shared/src/lib/serialize-cv-data.ts` — serializa items filtrados por niche a JSON embebible
  - Verificar: unit test que valida output JSON
- `packages/app-shared/tests/unit/components/FilterChips.test.ts` — AC-11, AC-12
- `packages/app-shared/tests/unit/lib/serialize-cv-data.test.ts`

#### Tests E2E

- `tests/feature/smoke/cv-filters.spec.ts` — AC-4, AC-6, AC-11, AC-13, AC-16, AC-19, AC-20
  - Verificar: `python devtools/run.py test_runner --module=feature --type=feature --env=local`

#### Specs / docs

- `docs/specs/cv-filters-query-params.md` — este documento

### Modificar

#### Schema + data en `packages/content/`

- `packages/content/src/schemas.ts` — agregar `seniority` a `ExperienceSchema`, `projectType` a `ProjectSchema`
  - Verificar: `pnpm exec tsc --noEmit` desde el package
  - Verificar: tests existentes de schema siguen pasando
- `packages/content/src/data/experiences/*.yaml` (9 archivos) — agregar `seniority` a cada uno
  - Verificar: `pnpm exec vitest run tests/unit/data/experiences.test.ts`
- `packages/content/src/data/projects/*.yaml` (N archivos) — agregar `projectType` a cada uno
  - Verificar: idem
- `packages/content/src/lib/build-stats.ts` — exportar la logica pura como funcion reusable client-side (mismo modulo, doble export server/client)
  - Verificar: tests existentes + nuevo test de uso desde browser context

#### Render en `packages/cv-pdf/`

- `packages/cv-pdf/src/lib/render-cv-html.ts` — agregar `data-*` attrs a items + embedded JSON + `<script>` referencing cv-filters bundle
  - Verificar: `pnpm exec vitest run` en cv-pdf
  - Verificar: snapshot del HTML output contiene attrs esperados
- `packages/cv-pdf/tests/unit/lib/render-cv-html.test.ts` — actualizar snapshots

#### Componentes compartidos

- `packages/app-shared/src/components/CvSections.astro` — agregar `data-*` attrs a cada item + embebed JSON + montar FilterChips + script defer
  - Verificar: `pnpm exec astro check` desde una app que lo use
- `packages/app-shared/src/components/AboutSection.astro` — idem para awards/publications
- `packages/app-shared/src/lib/get-niche-extras.ts` — `StatsBar` recibe `dataMode="dynamic"` para permitir recalculo

#### Apps (5 apps con CV: generic, fintech, architect, leader, vibe — hub queda fuera)

- `apps/generic/scripts/build-public-assets.mjs` — inyectar bundle `cv-filters.js` en public/
  - Verificar: `pnpm --filter @portfolio/generic run build` genera public/cv-filters.js
- `apps/fintech/scripts/build-public-assets.mjs` — idem
- `apps/architect/scripts/build-public-assets.mjs` — idem
- `apps/leader/scripts/build-public-assets.mjs` — idem
- `apps/vibe/scripts/build-public-assets.mjs` — idem
- `apps/generic/src/pages/about.astro` — pasar `enableFilters={true}` a CvSections
  - Verificar: `pnpm exec astro check` + screenshot E2E
- `apps/generic/src/pages/en/about.astro` — idem
- `apps/fintech/src/pages/about.astro` + `apps/fintech/src/pages/en/about.astro`
- `apps/architect/src/pages/about.astro` + `apps/architect/src/pages/en/about.astro`
- `apps/leader/src/pages/about.astro` + `apps/leader/src/pages/en/about.astro`
- `apps/vibe/src/pages/about.astro` + `apps/vibe/src/pages/en/about.astro`

#### Specs existentes

- `tests/feature/smoke/cv-screenshots.spec.ts` — agregar variante con filtros activos
  - Verificar: spec corre verde en stack local

### Eliminar

Nada se elimina. Es un feature aditivo.

## 8. Descomposicion para Paralelizacion

Plan Large -> activar descomposicion. Ver
`.claude/docs/plan-format-large/README.md` para reglas completas
(File Exclusivity, Interface Stability, Bounded Scope).

Tareas atomicas, paralelas por agente en git worktree:

### Tarea T1: Schema + data backfill (FUNDACIONAL, debe correr primero)

- **Archivos**: `packages/content/src/schemas.ts`, `packages/content/src/data/experiences/*.yaml` (9), `packages/content/src/data/projects/*.yaml` (N), `packages/content/tests/unit/schemas.test.ts`
- **AC referenciados**: AC-1, AC-2, AC-3
- **Depende de**: nada (raiz)
- **Paralelizable con**: ninguna (las demas dependen del schema actualizado)
- **Verify**: `pnpm --filter @portfolio/content run typecheck && pnpm --filter @portfolio/content run test`
- **Done**: schema acepta nuevos campos, 9+N YAMLs validados, tests pasan

### Tarea T2: Filter engine + bundle (paquete nuevo cv-filters)

- **Archivos**: TODO `packages/cv-filters/**` (paquete nuevo completo)
- **AC referenciados**: AC-4, AC-5, AC-6, AC-7, AC-8, AC-10, AC-11, AC-12, AC-13, AC-14, AC-15
- **Depende de**: T1 (necesita conocer schema final para tipar `Item`)
- **Paralelizable con**: T3 (no comparten archivos)
- **Verify**: `pnpm --filter @portfolio/cv-filters run test && pnpm --filter @portfolio/cv-filters run build && du -h dist/cv-filters.js` (esperado < 10kb gzip)
- **Done**: bundle compila < 10kb, tests unit verdes, coverage >= 80%

### Tarea T3: Render + data attrs (cv-pdf + app-shared)

- **Archivos**: `packages/cv-pdf/src/lib/render-cv-html.ts`, `packages/cv-pdf/tests/unit/lib/render-cv-html.test.ts`, `packages/app-shared/src/components/CvSections.astro`, `packages/app-shared/src/components/AboutSection.astro`, `packages/app-shared/src/components/FilterChips.astro` (nuevo), `packages/app-shared/src/components/FilterEmptyState.astro` (nuevo), `packages/app-shared/src/lib/serialize-cv-data.ts` (nuevo), `packages/app-shared/tests/unit/**`
- **AC referenciados**: AC-9, AC-16, AC-17, AC-18
- **Depende de**: T1 (necesita schema con seniority/projectType para serializar correctamente)
- **Paralelizable con**: T2 (no comparten archivos)
- **Verify**: `pnpm --filter @portfolio/cv-pdf run test && pnpm --filter @portfolio/app-shared run test && pnpm --filter @portfolio/app-shared run typecheck`
- **Done**: HTML output incluye data-* attrs + JSON embebed + script tag, snapshot tests actualizados

### Tarea T4: Apps integration (5 apps en paralelo)

- **Archivos**: por cada app `{generic,fintech,architect,leader,vibe}`:
  - `apps/<app>/scripts/build-public-assets.mjs`
  - `apps/<app>/src/pages/about.astro`
  - `apps/<app>/src/pages/en/about.astro`
- **AC referenciados**: AC-19, AC-20
- **Depende de**: T2 (bundle) + T3 (CvSections con nueva prop)
- **Paralelizable con**: T4a (generic), T4b (fintech), T4c (architect), T4d (leader), T4e (vibe) — entre si SI (file exclusivity total)
- **Verify por sub-tarea**: `pnpm --filter @portfolio/<app> run build && pnpm --filter @portfolio/<app> run typecheck`
- **Done**: 6 builds estaticos exitosos, cada cv.html incluye `<script src="/cv-filters.js" defer>` y data-* attrs

### Tarea T5: E2E spec nueva + actualizar existente

- **Archivos**: `tests/feature/smoke/cv-filters.spec.ts` (nuevo), `tests/feature/smoke/cv-screenshots.spec.ts` (actualizar)
- **AC referenciados**: AC-4, AC-6, AC-11, AC-13, AC-16, AC-19, AC-20
- **Depende de**: T4 (stack debe estar funcional)
- **Paralelizable con**: nada (E2E es el gate final)
- **Verify**: `python devtools/run.py docker up --env=local && python devtools/run.py test_runner --module=feature --type=feature --env=local`
- **Done**: 2 specs verde en stack local

### Diagrama de dependencias

```text
        T1 (schema+data)
       /                \
      T2 (filter engine)  T3 (render+data attrs)
       \                /
        T4 (5 apps - paralelas entre si: T4a..T4e)
              |
        T5 (E2E)
```

Limite practico: T4 puede correr con 5 agentes concurrentes (uno por app)
porque cada uno toca archivos exclusivos. T2 y T3 corren en 2 agentes
concurrentes despues de T1.

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] AC numerados (AC-1 a AC-20) y referenciados en cada test
- [ ] Schema final aprobado: seniority 5 valores, projectType 6 valores
- [ ] Backfill manual de los 9 experiences + N projects acordado con el usuario (revisar uno a uno)
- [ ] Tests TDD escritos y fallando (Red phase) para parse-params, matches-filter, ranges-intersect
- [ ] `pnpm install` sin warnings (nuevo workspace `cv-filters`)
- [ ] Docker stack arranca limpio (`pnpm run docker:up`)
- [ ] No hay breaking changes en APIs publicas de `@portfolio/content` (campos NUEVOS, no se renombran existentes)

### Definition of Done

- [ ] Todos los AC tienen al menos un test que los cubre y pasa
- [ ] Coverage per-file >= 80% en archivos modificados/creados (Vitest)
- [ ] `pnpm run typecheck` recursivo pasa (tsc + astro check)
- [ ] `pnpm run lint` (Biome) pasa
- [ ] `pnpm run build` exitoso en las 6 apps
- [ ] Bundle `cv-filters.js` < 10kb gzip (verificar con `gzip -c dist/cv-filters.js | wc -c`)
- [ ] Spec E2E nueva `cv-filters.spec.ts` verde en stack local
- [ ] Spec E2E existente `cv-screenshots.spec.ts` con casos filtrados verde
- [ ] Pre-commit + pre-push hooks pasan sin `SKIP_STEPS`
- [ ] CV HTML estatico (cv.html, cv-es.html, cv-en.html) inspeccionado: ATS scraper sin JS ve todos los items, chips ocultos
- [ ] Documentacion `.claude/docs/cv/` actualizada con la nueva capa de filtros
- [ ] Memoria engram guardada con resumen de implementacion + gotchas encontrados
